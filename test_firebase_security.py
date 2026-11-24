import unittest
from pathlib import Path

from firebase_integration import (
    AppIdentity,
    AuthorizationError,
    resolve_role,
    require_role,
    safe_storage_name,
    validate_upload,
)


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

    def test_rules_are_deny_by_default(self):
        for path in ("firestore.rules", "storage.rules"):
            text = Path(path).read_text(encoding="utf-8")
            self.assertIn("allow read, write: if false;", text)
            self.assertNotIn("allow read, write: if true;", text)


if __name__ == "__main__":
    unittest.main()
