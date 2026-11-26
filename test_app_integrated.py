import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from firebase_integration import AppIdentity
from quest_data import UNIT_CATALOG
from rag_pbl_single_agent import DiscoveryResult, PBLReview
from student_access import code_digest, generate_access_code


def _complete_current_scenario(at: AppTest) -> str:
    unit_name = at.session_state["hq_selected_unit"]
    scenario_id = at.session_state["hq_selected_scenario_id"]
    scenario = next(
        item
        for item in UNIT_CATALOG[unit_name]["scenarios"]
        if item["scenario_id"] == scenario_id
    )
    at.session_state["hq_submissions"] = {
        mission["id"]: {
            "selected_idx": mission.get("answer_index", 0),
            "is_correct": True,
            "rationale": "학생이 작성한 임상 판단 근거입니다.",
            "rationale_status": "개인 서술 완료",
            "ai_individual_feedback": "피드백 확인 완료",
        }
        for mission in scenario["missions"]
    }
    return unit_name


def _button_count(at: AppTest, key: str) -> int:
    return sum(1 for button in at.button if button.key == key)


def _demo_app():
    app = AppTest.from_file("app_integrated.py", default_timeout=30)
    app.secrets["firebase"] = {"enabled": False}
    return app.run()


class IntegratedAppTest(unittest.TestCase):
    def test_selecting_team_in_submission_opens_recording_instructions(self):
        identity = AppIdentity("student-test", "", "백합", "student", "1반", login_method="access_code")
        backend = Mock()
        backend.get_student_team.return_value = {"name": "햇살", "aliases": ["백합", "장미"]}
        backend.list_student_submissions.return_value = []
        at = AppTest.from_file("student_submission.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.session_state["hq_identity"] = identity.as_dict()
        with patch("firebase_integration.get_backend", return_value=backend):
            at.run()
            self.assertFalse(at.exception)
            self.assertFalse(any(b.label == "모의상황실습으로 이동" for b in at.button))
            at.radio(key="hq_attachment_submission_type").set_value("팀").run()
            self.assertFalse(at.exception)
            self.assertTrue(any(b.label == "모의상황실습으로 이동" for b in at.button))
            next(b for b in at.button if b.label == "이 화면에서 자료 첨부 계속").click().run()
            self.assertFalse(at.exception)
            self.assertFalse(any(b.label == "모의상황실습으로 이동" for b in at.button))
            backend.create_submission.assert_not_called()

    def test_stale_backend_shows_restart_instruction_before_writing_rubric(self):
        identity = AppIdentity("teacher-test", "teacher@example.test", "교사", "teacher")
        backend = Mock()
        backend.list_teacher_dashboard.return_value = {"users": [], "sessions": [], "submissions": [{
            "submission_id": "legacy-backend", "student_name": "학생", "class_id": "1반",
        }]}
        backend.list_class_teams.return_value = {}

        def old_save(teacher, submission_id, score, feedback, status):
            self.fail("An old server must not overwrite a detailed rubric.")

        backend.save_teacher_feedback = old_save
        at = AppTest.from_file("teacher_dashboard.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.secrets["authz"] = {"student_login_mode": "google"}
        at.session_state["hq_identity"] = identity.as_dict()
        with patch("firebase_integration.get_backend", return_value=backend):
            at.run()
            self.assertFalse(at.exception)
            self.assertTrue(any("서버를 재시작" in alert.value for alert in at.warning))
            at.button(key="rubric_legacy-backend").click().run()
            self.assertFalse(at.exception)
            self.assertTrue(next(b for b in at.button if b.label == "항목별 점수와 평가 저장").disabled)

    def test_dedicated_entrypoints_select_their_own_login_modes(self):
        for filename, code_mode in (("app_firebase_codes.py", True), ("app_firebase_google.py", False)):
            with self.subTest(filename=filename):
                at = AppTest.from_file(filename, default_timeout=30)
                at.secrets["firebase"] = {"enabled": True}
                at.secrets["authz"] = {"student_login_mode": "google" if code_mode else "access_code"}
                at.run()
                self.assertFalse(at.exception)
                self.assertEqual(any(w.label == "개별 접속코드" for w in at.text_input), code_mode)
                self.assertEqual(any(b.label == "Google 계정으로 학생 로그인" for b in at.button), not code_mode)
                self.assertTrue(any(b.label == "Google 계정으로 교사 로그인" for b in at.button))

    def test_teacher_opens_unit_specific_scoring_dialog(self):
        identity = AppIdentity("teacher-test", "teacher@example.test", "교사", "teacher")
        unit_name = next(iter(UNIT_CATALOG))
        submission_id = "d" * 32
        backend = Mock()
        backend.list_access_roster.return_value = []
        backend.list_class_teams.return_value = {}
        backend.list_teacher_dashboard.return_value = {"users": [], "sessions": [], "submissions": [{
            "submission_id": submission_id, "unit_name": unit_name, "student_name": "백합",
            "class_id": "1반", "team_name": "햇살", "access_number": "1반-001",
            "submission_type": "팀", "activity": "final_simulation", "reflection": "공동 답안",
        }]}
        at = AppTest.from_file("teacher_dashboard.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.secrets["authz"] = {"student_login_mode": "access_code"}
        at.session_state["hq_identity"] = identity.as_dict()
        with patch("firebase_integration.get_backend", return_value=backend):
            at.run()
            at.button(key=f"rubric_{submission_id}").click().run()
            self.assertFalse(at.exception)
            self.assertTrue(any(item.label == "이 단원의 학습 목표" for item in at.expander))
            self.assertTrue(any(item.label == "음성 전달과 답안 일치" for item in at.selectbox))
            for label in ("상황 분석과 수업 근거", "환자 안전과 우선순위", "모둠 합의와 역할", "음성 전달과 답안 일치"):
                next(item for item in at.selectbox if item.label == label).set_value(25)
            next(button for button in at.button if button.label == "항목별 점수와 평가 저장").click().run()
            self.assertFalse(at.exception)
            backend.save_teacher_feedback.assert_called_once_with(
                identity, submission_id, 100, "", "reviewing",
                rubric_scores={"concept": 25, "safety": 25, "collaboration": 25, "communication": 25},
            )

    def test_teacher_dashboard_opens_and_saves_team_members(self):
        identity = AppIdentity("teacher-test", "teacher@example.test", "교사", "teacher")
        members = {"a" * 32: "백합", "b" * 32: "장미"}
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        backend = Mock()
        backend.list_teacher_dashboard.return_value = {"users": [], "submissions": [], "sessions": []}
        backend.list_access_roster.return_value = [
            {"uid": uid, "alias": alias, "class_id": "1반", "access_number": f"1반-{number:03d}", "expires_at": expires}
            for number, (uid, alias) in enumerate(members.items(), start=1)
        ]
        backend.list_class_teams.return_value = {}
        at = AppTest.from_file("teacher_dashboard.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.secrets["authz"] = {"student_login_mode": "access_code", "class_ids": ["1반"]}
        at.session_state["hq_identity"] = identity.as_dict()
        with patch("firebase_integration.get_backend", return_value=backend):
            at.run()
            self.assertFalse(at.exception)
            self.assertTrue(any(item.label == "모둠 편성 관리" for item in at.expander))
            next(item for item in at.multiselect if item.label == "모둠원 꽃 별명").set_value(list(members))
            next(button for button in at.button if button.label == "모둠 편성 저장").click().run()
            self.assertFalse(at.exception)
            backend.save_class_team.assert_called_once_with(identity, "1반", "햇살", list(members))

    def test_google_dashboard_and_code_dashboard_offer_the_same_team_workflow(self):
        identity = AppIdentity("teacher-test", "teacher@example.test", "교사", "teacher")
        backend = Mock()
        backend.list_teacher_dashboard.return_value = {"users": [
            {"uid": "google-a", "role": "student", "class_id": "1반", "display_name": "학생A", "student_number": "20101"},
            {"uid": "google-b", "role": "student", "class_id": "1반", "display_name": "학생B", "student_number": "20102"},
        ], "submissions": [], "sessions": []}
        backend.list_class_teams.return_value = {}
        at = AppTest.from_file("teacher_dashboard.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.secrets["authz"] = {"student_login_mode": "google", "class_ids": ["1반"]}
        at.session_state["hq_identity"] = identity.as_dict()
        with patch("firebase_integration.get_backend", return_value=backend):
            at.run()
            self.assertFalse(at.exception)
            widget = next(item for item in at.multiselect if item.label == "모둠원 학번·이름")
            self.assertEqual(widget.options, ["20101 학생A", "20102 학생B"])
            widget.set_value(["google-a", "google-b"])
            next(button for button in at.button if button.label == "모둠 편성 저장").click().run()
            self.assertFalse(at.exception)
            backend.save_class_team.assert_called_once_with(identity, "1반", "햇살", ["google-a", "google-b"])
            backend.list_access_roster.assert_not_called()

    def test_team_member_sees_submitted_team_answer_and_feedback(self):
        identity = AppIdentity("b" * 32, "", "장미", "student", "1반", access_number="1반-002")
        backend = Mock()
        backend.get_student_team.return_value = None
        backend.list_student_submissions.return_value = [{
            "submission_id": "d" * 32, "student_uid": "a" * 32,
            "team_member_uids": ["a" * 32, identity.uid],
            "unit_name": "감염관리", "team_name": "햇살", "team_members": "백합, 장미",
            "activity": "final_simulation", "reflection": "모둠이 합의한 공동 답안",
            "teacher_feedback": "모둠 평가 완료",
        }]
        at = AppTest.from_file("student_submission.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.session_state["hq_identity"] = identity.as_dict()
        with patch("firebase_integration.get_backend", return_value=backend):
            at.run()
        self.assertFalse(at.exception)
        self.assertTrue(any(item.value == "모둠이 합의한 공동 답안" for item in at.text))
        self.assertTrue(any("모둠 평가 완료" in item.value for item in at.caption))
        with patch("firebase_integration.get_backend", return_value=backend):
            at.button(key=f"open_receipt_{'d' * 32}").click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["hq_identity"]["uid"], identity.uid)
            self.assertTrue(any(item.value == "제출 내용 확인" for item in at.title))
            self.assertTrue(any(item.value == "모둠이 합의한 공동 답안" for item in at.text))
            next(button for button in at.button if button.label == "제출 화면과 전체 기록으로 돌아가기").click().run()
            self.assertFalse(at.exception)
            self.assertTrue(any(item.value == "수행평가 자료 제출" for item in at.title))

    def test_public_access_code_app_keeps_student_login_mode(self):
        code = generate_access_code()
        student_uid = "a" * 32
        credential = {
            "class_id": "1반", "access_number": "1반-001",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        }
        backend = Mock()
        backend.find_student_access.return_value = (student_uid, credential)
        backend.verify_student_access.return_value = credential
        backend.available_student_aliases.return_value = ["백합", "장미"]
        backend.get_learning_snapshot.return_value = {}

        def claim(uid, hashed, alias):
            self.assertEqual((uid, hashed), (student_uid, code_digest(code)))
            credential["alias"] = alias
            return True

        backend.claim_student_alias.side_effect = claim
        at = AppTest.from_file("app_firebase.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.secrets["authz"] = {"student_login_mode": "access_code"}
        with patch("firebase_integration.get_backend", return_value=backend):
            at.run()
            self.assertFalse(at.exception)
            self.assertFalse(any(button.label == "Google 계정으로 학생 로그인" for button in at.button))
            next(entry for entry in at.text_input if entry.label == "개별 접속코드").set_value(code)
            next(button for button in at.button if button.label == "학생 로그인").click().run()
            self.assertFalse(at.exception)
            next(entry for entry in at.selectbox if entry.label == "꽃 별명").select("백합")
            next(button for button in at.button if button.label == "이 별명으로 시작").click().run()
            self.assertFalse(at.exception)
            registered = at.session_state["hq_identity"]
            self.assertEqual((registered["name"], registered["login_method"]), ("백합", "access_code"))
            self.assertNotIn("access_number", registered)
            self.assertTrue(any(caption.value == "백합" for caption in at.sidebar.caption))
            self.assertFalse(any("1반-001" in caption.value for caption in at.sidebar.caption))
            self.assertEqual((registered["email"], registered["student_number"]), ("", ""))
            at.secrets["authz"] = {"student_login_mode": "google"}
            at.run()
            self.assertFalse(at.exception)
            self.assertFalse(any(button.label == "Google 계정으로 학생 로그인" for button in at.button))
            self.assertEqual(at.session_state["hq_identity"]["uid"], student_uid)

    def test_final_team_form_requires_audio(self):
        unit_name, unit = next(iter(UNIT_CATALOG.items()))
        scenario = unit["scenarios"][0]
        identity = AppIdentity("test-uid", "student@example.test", "학생", "student", "1반", "123")
        at = AppTest.from_file("app_rag_pbl.py", default_timeout=30)
        for key, value in {
            "hq_firebase_mode": True,
            "hq_identity": identity.as_dict(),
            "hq_selected_unit": unit_name,
            "hq_selected_scenario_id": scenario["scenario_id"],
            "hq_submissions": {m["id"]: {"is_correct": True, "rationale": "판단 근거"} for m in scenario["missions"]},
            "ragpbl_last_unit": unit_name,
            "ragpbl_selected_id": "A",
            "ragpbl_discovery": DiscoveryResult(
                knowledge_level="기초", level_reason="개념 확인", question_summary="질문 요약",
                key_concepts=["환자 안전"], safety_note="교육용",
                scenarios=[
                    {"id": letter, "title": f"상황 {letter}", "hospital_situation": "가상 상황",
                     "why_this_fits": "학습 단원", "concepts_to_use": ["환자 안전"],
                     "clinical_clues": ["핵심 단서"], "pbl_task": "판단 근거 설명", "evidence_summary": "안전 원칙"}
                    for letter in "ABC"
                ],
            ),
            "ragpbl_review": PBLReview(
                knowledge_alignment="안전 원칙", strengths=["경청"], evidence_gaps=[],
                safety_feedback="교육용", coaching_questions=[], revision_task="근거 보완",
                concept_score=2, reasoning_score=2, evidence_score=2, reflection_score=2,
            ),
        }.items():
            at.session_state[key] = value

        with patch("firebase_integration.get_backend") as get_backend:
            backend = get_backend.return_value
            backend.get_student_team.return_value = {"name": "햇살", "aliases": ["학생", "학생B"]}
            backend.get_team_final_receipt.return_value = None
            at.run()
            self.assertFalse(at.exception)
            self.assertTrue(any("최종 답안" in entry.value for entry in at.warning))
            self.assertEqual(len(at.get("audio_input")), 1)
            next(entry for entry in at.text_area if "합의한 모둠" in entry.label).set_value("모둠 최종 답안")
            next(button for button in at.button if button.label == "모둠 답안과 음성을 교사에게 제출").click().run()
            self.assertTrue(any("음성을 첨부" in entry.value for entry in at.error))
            backend.create_submission.assert_not_called()

    def test_receipt_displays_only_records_from_current_student(self):
        owned_id = "a" * 32
        identity = AppIdentity("test-uid", "student@example.test", "학생", "student", "1반", "123")
        backend = Mock()
        backend.list_student_submissions.return_value = [{
            "submission_id": owned_id,
            "unit_name": "감염관리",
            "files": [{"name": "학습기록.xlsx"}],
        }]
        at = AppTest.from_file("student_submission.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.session_state["hq_identity"] = identity.as_dict()
        with patch("firebase_integration.get_backend", return_value=backend):
            at.query_params["receipt"] = "b" * 32
            at.run()
            self.assertFalse(at.exception)
            self.assertTrue(any("확인할 수 없습니다" in entry.value for entry in at.warning))
            self.assertFalse(any("학습기록.xlsx" in entry.value for entry in at.text))
            at.query_params["receipt"] = owned_id
            at.run()
            self.assertFalse(at.exception)
            self.assertTrue(any("학습기록.xlsx" in entry.value for entry in at.text))
            backend.list_student_submissions.assert_called_with(identity)

    def test_firebase_entrypoint_requires_login(self):
        at = AppTest.from_file("app_firebase.py", default_timeout=30)
        at.secrets["firebase"] = {"enabled": True}
        at.run()

        self.assertFalse(at.exception)
        self.assertTrue(any("학생 로그인" in button.label for button in at.button))

    def test_firebase_student_requires_correct_answers_and_cannot_edit_feedback(self):
        def signed_in(settings):
            import streamlit as st

            identity = AppIdentity("test-uid", "student@example.test", "학생", "student", "1반", "123")
            st.session_state["hq_firebase_mode"] = True
            st.session_state["hq_identity"] = identity.as_dict()
            st.session_state["hq_student_label"] = "123 학생"
            st.session_state["hq_loaded_unit"] = st.session_state.get("hq_selected_unit")
            return identity

        with (
            patch("integrated_app_runtime.require_authenticated_identity", side_effect=signed_in),
            patch("integrated_app_runtime.restore_learning_unit"),
            patch("integrated_app_runtime.persist_current_learning_state"),
        ):
            at = AppTest.from_file("app_firebase.py", default_timeout=30)
            at.secrets["firebase"] = {"enabled": True}
            at.run()
            self.assertFalse(at.exception)
            at.button(key="hq_next_learning").click().run()
            self.assertTrue(next(button for button in at.button if button.label == "중급 학습").disabled)
            self.assertTrue(next(button for button in at.button if button.label == "심화 학습").disabled)
            _complete_current_scenario(at)
            answers = at.session_state["hq_submissions"]
            next(iter(answers.values()))["is_correct"] = False
            at.run()
            self.assertEqual(_button_count(at, "integrated_simulation_start"), 0)
            next(iter(answers.values()))["is_correct"] = True
            at.session_state["hq_nav_view"] = "STEP 03 · 팀 협력 & 교사 피드백"
            at.run()
            self.assertFalse(at.exception)
            self.assertEqual(_button_count(at, "integrated_simulation_start"), 1)
            self.assertFalse(any("교사 직접 코멘트" in expander.label for expander in at.expander))

    def test_simulation_lab_unlocks_only_after_all_missions(self):
        at = _demo_app()
        self.assertFalse(at.exception)
        self.assertEqual(_button_count(at, "integrated_simulation_start"), 0)

        _complete_current_scenario(at)
        at.run(timeout=30)

        self.assertFalse(at.exception)
        self.assertEqual(_button_count(at, "integrated_simulation_start"), 1)

    def test_launch_hands_unit_to_rag_page_and_clears_stale_unit_state(self):
        at = _demo_app()
        unit_name = _complete_current_scenario(at)
        at.session_state["ragpbl_last_unit"] = "이전 단원"
        at.session_state["ragpbl_discovery"] = "stale result"
        at.run(timeout=30)

        at.button(key="integrated_simulation_start").click().run(timeout=30)

        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["ragpbl_unit"], unit_name)
        self.assertEqual(at.session_state["ragpbl_last_unit"], unit_name)
        self.assertEqual(at.session_state["ragpbl_entry_source"], "mission_room")
        self.assertIsNone(at.session_state["ragpbl_discovery"])


if __name__ == "__main__":
    unittest.main()
