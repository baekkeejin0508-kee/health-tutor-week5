import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from firebase_integration import (
    AppIdentity,
    AuthorizationError,
    FirebaseBackend,
    FirebaseSettings,
    resolve_role,
    require_role,
    safe_storage_name,
    validate_upload,
)
from student_access import FLOWER_ALIASES, access_expiration, code_digest, distribution_mark, generate_access_code


class FirebaseAuthorizationTest(unittest.TestCase):
    def setUp(self):
        self.student = AppIdentity(
            uid="student-a",
            email="student@example.com",
            name="학생A",
            role="student",
            class_id="1반",
            student_number="101",
        )
        self.teacher = AppIdentity(
            uid="teacher-a",
            email="teacher@example.com",
            name="교사A",
            role="teacher",
        )

    def test_teacher_allowlist_is_case_insensitive(self):
        self.assertEqual(resolve_role("Teacher@Example.com", ["teacher@example.com"]), "teacher")
        self.assertEqual(resolve_role("student@example.com", ["teacher@example.com"]), "student")

    def test_student_cannot_access_teacher_operation(self):
        with self.assertRaises(AuthorizationError):
            require_role(self.student, "teacher")
        require_role(self.teacher, "teacher")

    def test_student_cannot_access_another_students_record(self):
        require_role(self.student, "student", owner_uid="student-a")
        with self.assertRaises(AuthorizationError):
            require_role(self.student, "student", owner_uid="student-b")
        require_role(self.teacher, "teacher", owner_uid="student-b")

    def test_upload_allowlist_and_limits(self):
        self.assertIsNone(validate_upload("report.pdf", "application/pdf", 1000))
        self.assertIsNotNone(validate_upload("script.exe", "application/octet-stream", 1000))
        self.assertIsNotNone(validate_upload("large.pdf", "application/pdf", 21 * 1024 * 1024))
        self.assertEqual(safe_storage_name("../환자 자료?.pdf"), "환자_자료_.pdf")

    def test_student_attachment_and_team_submission_reach_teacher_dashboard(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend._firestore = SimpleNamespace(SERVER_TIMESTAMP="server-time")
        backend.bucket = Mock()
        backend.bucket.name = "test-bucket"
        backend.db = Mock()
        collection = backend.db.collection.return_value
        document = collection.document.return_value
        names_and_types = [
            ("학습 기록.xlsx", "application/octet-stream"),
            ("recording.wav", "audio/x-wav"),
            ("image.png", "image/png"),
            ("video.mp4", "video/mp4"),
            ("성찰.txt", "text/plain; charset=utf-8"),
        ]
        files = [(name, mime, b"test bytes") for name, mime in names_and_types]
        with self.assertRaises(AuthorizationError):
            backend.create_submission(self.teacher, {}, files)
        with self.assertRaises(ValueError):
            backend.create_submission(self.student, {"activity": "final_simulation"}, files)
        backend.bucket.blob.assert_not_called()
        submission_id = backend.create_submission(self.student, {"unit_name": "단원"}, files)
        record = document.set.call_args.args[0]
        self.assertEqual(record["student_uid"], self.student.uid)
        self.assertEqual(record["submission_id"], submission_id)
        self.assertEqual(record["class_id"], "1반")
        self.assertEqual([value["name"] for value in record["files"]], [name for name, _ in names_and_types])
        self.assertTrue(record["files"][0]["content_type"].endswith("spreadsheetml.sheet"))
        self.assertEqual(record["files"][1]["content_type"], "audio/wav")
        collection.stream.return_value = [SimpleNamespace(to_dict=lambda: record)]
        self.assertEqual(backend.list_teacher_dashboard(self.teacher)["submissions"], [record])
        with self.assertRaises(AuthorizationError):
            backend.save_teacher_feedback(self.student, submission_id, 90, "평가", "evaluated")
        backend.save_teacher_feedback(self.teacher, submission_id, 90, "평가", "evaluated")
        self.assertEqual(document.update.call_args.args[0]["teacher_feedback"], "평가")
        backend.get_student_team = Mock(return_value={
            "name": "햇살", "member_uids": [self.student.uid, "google-student-b"], "aliases": ["학생A", "학생B"],
        })
        document.get.return_value.to_dict.return_value = None
        backend.create_submission(self.student, {
            "activity": "final_simulation", "submission_type": "팀", "reflection": "모둠 결론",
        }, [files[1]])
        final_record = document.create.call_args.args[0]
        self.assertEqual(final_record["activity"], "final_simulation")
        self.assertEqual(final_record["team_member_uids"], [self.student.uid, "google-student-b"])
        self.assertEqual(final_record["team_name"], "햇살")

    def test_invalid_attachment_cannot_leave_half_uploaded_record(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend.bucket = Mock()
        with self.assertRaises(ValueError):
            backend.create_submission(self.student, {}, [
                ("photo.png", "image/png", b"sample"),
                ("report.xlsx", "text/html", b"sample"),
            ])
        backend.bucket.blob.assert_not_called()

    def test_codes_are_normalized_and_expire_after_three_calendar_years(self):
        code = generate_access_code()
        self.assertTrue(code_digest(code))
        self.assertEqual(code_digest(code.lower().replace("-", " ")), code_digest(code))
        self.assertFalse(code_digest("백합"))
        self.assertEqual(len(set(FLOWER_ALIASES)), 100)
        issued = datetime(2028, 2, 29, tzinfo=timezone.utc)
        self.assertEqual(access_expiration(issued), datetime(2031, 2, 28, tzinfo=timezone.utc))

    def test_issuance_and_rotation_store_only_hashes(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend.settings = FirebaseSettings(student_login_mode="access_code")
        backend.db = Mock()
        backend._firestore = SimpleNamespace(transactional=lambda callback: callback)
        transaction = backend.db.transaction.return_value
        reference = backend.db.collection.return_value.document.return_value
        reference.get.return_value.to_dict.return_value = {"issued": 5}

        with self.assertRaises(AuthorizationError):
            backend.issue_student_access_codes(self.student, "1반", 2)
        issued = backend.issue_student_access_codes(self.teacher, "1반", 2)
        issued_uid = backend.db.collection.return_value.document.call_args.args[0]
        self.assertEqual(len({row["배부 표식"] for row in issued}), 2)
        self.assertEqual(issued[-1]["배부 표식"], distribution_mark(issued_uid))
        saved = transaction.create.call_args_list[-1].args[1]
        self.assertNotIn("access_number", saved)
        self.assertEqual(saved["code_hash"], code_digest(issued[-1]["접속코드"]))
        self.assertNotIn(issued[-1]["접속코드"], str(saved))

        reference.get.return_value.to_dict.return_value = {**saved, "alias": "백합"}
        refreshed = backend.reissue_student_access_code(self.teacher, issued_uid)
        self.assertEqual(refreshed["배부 표식"], issued[-1]["배부 표식"])
        change = transaction.update.call_args.args[1]
        self.assertEqual(change, {"code_hash": code_digest(refreshed["접속코드"])})
        reference.get.return_value.to_dict.return_value = {**saved, **change, "alias": "백합"}
        self.assertIsNone(backend.verify_student_access("a" * 32, saved["code_hash"]))
        self.assertEqual(backend.verify_student_access("a" * 32, change["code_hash"])["alias"], "백합")
        reference.get.return_value.to_dict.return_value["expires_at"] = datetime.now(timezone.utc) - timedelta(days=1)
        self.assertIsNone(backend.verify_student_access("a" * 32, change["code_hash"]))
        reference.get.return_value.to_dict.return_value = {"issued": 19}
        with self.assertRaisesRegex(ValueError, "최대 20명"):
            backend.issue_student_access_codes(self.teacher, "1반", 2)
        self.assertTrue(backend.issue_student_access_codes(self.teacher, "1반", 1)[0]["배부 표식"].startswith("HQ-"))
        self.assertEqual(transaction.set.call_args.args[1]["issued"], 20)

    def test_alias_claim_prevents_duplicates_and_profile_has_no_real_identity_fields(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend.settings = FirebaseSettings(student_login_mode="access_code")
        backend._firestore = SimpleNamespace(transactional=lambda callback: callback, SERVER_TIMESTAMP="server-time")
        backend.db = Mock()
        reference = backend.db.collection.return_value.document.return_value
        hashed = code_digest(generate_access_code())
        reference.get.return_value.to_dict.return_value = {
            "class_id": "1반", "access_number": "1반-007", "code_hash": hashed,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
        }
        transaction = backend.db.transaction.return_value
        reference.get.return_value.exists = True
        self.assertFalse(backend.claim_student_alias("a" * 32, hashed, "백합"))
        transaction.create.assert_not_called()

        reference.get.return_value.exists = False
        self.assertTrue(backend.claim_student_alias("a" * 32, hashed, "백합"))
        profile = transaction.create.call_args.args[1]
        self.assertEqual(profile["display_name"], "백합")
        self.assertNotIn("student_number", profile)
        self.assertNotIn("email", profile)
        self.assertNotIn("code_hash", profile)
        self.assertNotIn("access_number", profile)
        self.assertEqual(profile["login_method"], "access_code")

    def test_alias_submission_uses_the_teacher_assigned_team(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend._firestore = SimpleNamespace(SERVER_TIMESTAMP="server-time")
        backend.db = Mock()
        backend.get_student_team = Mock(return_value=None)
        student = AppIdentity("a" * 32, "", "백합", "student", "1반", access_number="1반-001")
        fields = {"submission_type": "팀", "reflection": "함께 도출한 결론"}
        with self.assertRaises(ValueError):
            backend.create_submission(student, {**fields, "team_name": "임의 모둠"}, [])
        backend.get_student_team.return_value = {
            "name": "햇살", "member_uids": [student.uid, "b" * 32], "aliases": ["백합", "장미"],
        }
        backend.create_submission(student, {
            **fields, "team_name": "임의 모둠", "team_members": "실명은 사용하지 않음"
        }, [])
        record = backend.db.collection.return_value.document.return_value.set.call_args.args[0]
        self.assertEqual(record["student_name"], "백합")
        self.assertEqual(record["team_name"], "햇살")
        self.assertEqual(record["team_members"], "백합, 장미")
        self.assertEqual(record["team_member_uids"], [student.uid, "b" * 32])
        self.assertEqual(record["login_method"], "access_code")
        self.assertNotIn("access_number", record)
        self.assertNotIn("student_email", record)
        self.assertNotIn("student_number", record)

    def test_teacher_can_assign_four_students_but_not_duplicate_membership(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend.settings = FirebaseSettings(student_login_mode="access_code")
        backend._firestore = SimpleNamespace(transactional=lambda callback: callback)
        backend.db = Mock()
        members = [letter * 32 for letter in "abcd"]
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        backend.db.get_all.return_value = [
            SimpleNamespace(id=uid, to_dict=lambda alias=alias: {
                "alias": alias, "class_id": "1반", "expires_at": expires,
            })
            for uid, alias in zip(members, ["백합", "장미", "라벤더", "수국"])
        ]
        ref = backend.db.collection.return_value.document.return_value
        ref.get.return_value.to_dict.return_value = {}
        with self.assertRaises(AuthorizationError):
            backend.save_class_team(self.student, "1반", "햇살", members)
        backend.save_class_team(self.teacher, "1반", "햇살", members)
        saved = backend.db.transaction.return_value.set.call_args.args[1]
        self.assertEqual(saved["teams"]["햇살"]["aliases"], ["백합", "장미", "라벤더", "수국"])
        ref.get.return_value.to_dict.return_value = saved
        with self.assertRaisesRegex(ValueError, "이미 햇살"):
            backend.save_class_team(self.teacher, "1반", "구름", [members[0], "e" * 32])
        outsider = AppIdentity("e" * 32, "", "민들레", "student", "1반", access_number="1반-005")
        self.assertIsNone(backend.get_student_team(outsider))

    def test_teacher_can_assign_google_students_without_mixing_code_rosters(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend.settings = FirebaseSettings(student_login_mode="google")
        backend._firestore = SimpleNamespace(transactional=lambda callback: callback)
        backend.db = Mock()
        member_ids = ["1000001", "1000002"]
        backend.db.get_all.return_value = [
            SimpleNamespace(id=uid, to_dict=lambda i=i: {
                "display_name": f"학생{i}", "student_number": f"2010{i}", "class_id": "1반", "role": "student",
            })
            for i, uid in enumerate(member_ids, start=1)
        ]
        ref = backend.db.collection.return_value.document.return_value
        ref.get.return_value.to_dict.return_value = {}
        backend.save_class_team(self.teacher, "1반", "햇살", member_ids)
        self.assertEqual(backend.db.collection.call_args_list[0].args, ("student_teams_google",))
        self.assertEqual(backend.db.collection.call_args_list[1].args, ("users",))
        saved = backend.db.transaction.return_value.set.call_args.args[1]
        self.assertEqual(saved["teams"]["햇살"]["aliases"], ["학생1", "학생2"])

    def test_team_final_is_created_once_and_shared_with_submitting_team(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend._firestore = SimpleNamespace(SERVER_TIMESTAMP="server-time")
        backend.db = Mock()
        backend.bucket = Mock(name="bucket")
        backend.bucket.name = "test-bucket"
        lily = AppIdentity("a" * 32, "", "백합", "student", "1반", access_number="1반-001")
        rose = AppIdentity("b" * 32, "", "장미", "student", "1반", access_number="1반-002")
        backend.get_student_team = Mock(return_value={
            "name": "햇살", "member_uids": [lily.uid, rose.uid], "aliases": ["백합", "장미"],
        })
        doc = backend.db.collection.return_value.document.return_value
        doc.id = "d" * 32
        doc.get.return_value.to_dict.return_value = None
        fields = {"activity": "final_simulation", "unit_name": "감염관리", "submission_type": "팀", "reflection": "공동 답안"}
        with self.assertRaises(ValueError):
            backend.create_submission(lily, fields, [])
        receipt = backend.create_submission(lily, fields, [("recording.wav", "audio/wav", b"test audio")])
        record = doc.create.call_args.args[0]
        self.assertEqual(record["team_name"], "햇살")
        self.assertEqual(record["student_name"], "백합")
        self.assertEqual(record["files"][0]["content_type"], "audio/wav")
        doc.get.return_value.to_dict.return_value = record
        self.assertEqual(backend.get_team_final_receipt(rose, "감염관리", "햇살"), receipt)
        self.assertEqual(backend.create_submission(rose, fields, [("recording.wav", "audio/wav", b"new audio")]), receipt)
        doc.create.assert_called_once()
        backend.bucket.blob.assert_called_once()

    def test_rubric_saves_item_scores_and_calculates_total_on_server(self):
        backend = FirebaseBackend.__new__(FirebaseBackend)
        backend._firestore = SimpleNamespace(SERVER_TIMESTAMP="server-time")
        backend.db = Mock()
        doc = backend.db.collection.return_value.document.return_value
        doc.get.return_value.to_dict.return_value = {"activity": "final_simulation", "submission_type": "팀"}
        scores = {"concept": 25, "safety": 20, "collaboration": 15, "communication": 10}
        with self.assertRaises(ValueError):
            backend.save_teacher_feedback(self.teacher, "team", 100, "확인", "evaluated",
                                          rubric_scores={**scores, "communication": 24})
        doc.update.assert_not_called()
        backend.save_teacher_feedback(self.teacher, "team", 100, "확인", "evaluated", rubric_scores=scores)
        saved = doc.update.call_args.args[0]
        self.assertEqual(saved["rubric_score"], 70)
        self.assertEqual(saved["rubric_details"], {"id": "team_simulation_v1", "scores": scores})
        self.assertEqual(saved["teacher_feedback"], "확인")

    def test_rules_are_deny_by_default(self):
        for path in ("firestore.rules", "storage.rules"):
            text = Path(path).read_text(encoding="utf-8")
            self.assertIn("allow read, write: if false;", text)
            self.assertNotIn("allow read, write: if true;", text)


if __name__ == "__main__":
    unittest.main()
