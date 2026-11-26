"""Firebase authentication context, privileged storage, and authorization guards.

The Streamlit app is the only data client. Firestore and Storage rules therefore
deny direct browser access, while every Admin SDK operation is guarded again in
Python by the authenticated user's role and UID.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import uuid
from pathlib import PurePosixPath
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Iterable, Mapping

import streamlit as st

from evaluation_rubrics import rubric_for_submission, validate_rubric_scores

from student_access import (
    FLOWER_ALIASES,
    MAX_CODES_PER_CLASS,
    TEAM_NAMES,
    access_expiration,
    code_digest,
    distribution_mark,
    generate_access_code,
    record_uses_access_code,
)


DEFAULT_CLASSES = ("1반", "2반", "3반", "4반", "5반")
_firebase_app_init_lock = Lock()
ALLOWED_UPLOAD_TYPES = {
    "application/pdf": 20 * 1024 * 1024,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 20 * 1024 * 1024,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": 20 * 1024 * 1024,
    "image/jpeg": 20 * 1024 * 1024,
    "image/png": 20 * 1024 * 1024,
    "audio/mpeg": 25 * 1024 * 1024,
    "audio/wav": 25 * 1024 * 1024,
    "audio/x-wav": 25 * 1024 * 1024,
    "audio/webm": 25 * 1024 * 1024,
    "video/mp4": 100 * 1024 * 1024,
    "video/webm": 100 * 1024 * 1024,
    "text/plain": 1024 * 1024,
}
UPLOAD_TYPES_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".mp4": "video/mp4",
    ".webm": "video/webm", ".txt": "text/plain",
}


class FirebaseConfigurationError(RuntimeError):
    """Raised when Firebase is enabled but its private server config is incomplete."""


class AuthorizationError(PermissionError):
    """Raised before a privileged Firebase operation when the role check fails."""


@dataclass(frozen=True)
class FirebaseSettings:
    enabled: bool = False
    project_id: str = ""
    storage_bucket: str = ""
    service_account: dict[str, Any] = field(default_factory=dict)
    teacher_emails: tuple[str, ...] = ()
    class_ids: tuple[str, ...] = DEFAULT_CLASSES
    student_login_mode: str = "google"

    @property
    def configured(self) -> bool:
        required = {"project_id", "client_email", "private_key", "token_uri"}
        return bool(
            self.enabled
            and self.project_id
            and self.storage_bucket
            and required.issubset(self.service_account)
        )


@dataclass(frozen=True)
class AppIdentity:
    uid: str
    email: str
    name: str
    role: str
    class_id: str = ""
    student_number: str = ""
    access_number: str = ""
    login_method: str = "google"

    @property
    def uses_access_code(self) -> bool:
        return self.login_method == "access_code" or bool(self.access_number)

    def as_dict(self) -> dict[str, str]:
        fields = dataclasses.asdict(self)
        if self.uses_access_code:
            fields.pop("access_number", None)
            fields["login_method"] = "access_code"
        return fields


def _plain_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, Any] = {}
    for key, item in value.items():
        if hasattr(item, "to_dict"):
            item = item.to_dict()
        result[str(key)] = item
    return result


def load_firebase_settings() -> FirebaseSettings:
    """Read non-secret flags plus private credentials from Streamlit Secrets."""
    try:
        firebase_section = _plain_mapping(st.secrets.get("firebase", {}))
        authz_section = _plain_mapping(st.secrets.get("authz", {}))
    except (FileNotFoundError, KeyError):
        return FirebaseSettings()

    service_account = _plain_mapping(firebase_section.get("service_account", {}))
    if service_account.get("private_key"):
        service_account["private_key"] = str(service_account["private_key"]).replace("\\n", "\n")

    teachers = tuple(
        sorted(
            {
                str(email).strip().casefold()
                for email in authz_section.get("teacher_emails", [])
                if str(email).strip()
            }
        )
    )
    classes = tuple(
        str(value).strip()
        for value in authz_section.get("class_ids", DEFAULT_CLASSES)
        if str(value).strip()
    ) or DEFAULT_CLASSES

    login_mode = (st.session_state.get("hq_fixed_student_login_mode") or os.environ.get(
        "HEALTH_QUEST_STUDENT_LOGIN_MODE", str(authz_section.get("student_login_mode", "google"))
    )).strip().lower()
    if login_mode not in {"google", "access_code"}:
        raise FirebaseConfigurationError("학생 로그인 방식은 google 또는 access_code여야 합니다.")

    return FirebaseSettings(
        enabled=bool(firebase_section.get("enabled", False)),
        project_id=str(firebase_section.get("project_id", "")).strip(),
        storage_bucket=str(firebase_section.get("storage_bucket", "")).strip().removeprefix("gs://"),
        service_account=service_account,
        teacher_emails=teachers,
        class_ids=classes,
        student_login_mode=login_mode,
    )


def resolve_role(email: str, teacher_emails: Iterable[str]) -> str:
    normalized = email.strip().casefold()
    allowed = {item.strip().casefold() for item in teacher_emails}
    return "teacher" if normalized and normalized in allowed else "student"


def require_role(identity: AppIdentity, *allowed_roles: str, owner_uid: str | None = None) -> None:
    if identity.role not in allowed_roles:
        raise AuthorizationError("이 작업을 수행할 권한이 없습니다.")
    if owner_uid is not None and identity.role != "teacher" and identity.uid != owner_uid:
        raise AuthorizationError("다른 학생의 자료에는 접근할 수 없습니다.")


def normalize_upload_type(filename: str, content_type: str) -> str:
    extension = PurePosixPath(filename).suffix.lower()
    expected = UPLOAD_TYPES_BY_EXTENSION.get(extension)
    supplied = content_type.partition(";")[0].strip().lower()
    if expected is None:
        return ""
    if supplied in {"", "application/octet-stream", expected}:
        return expected
    if extension == ".wav" and supplied in {"audio/x-wav", "audio/wave"}:
        return expected
    if extension == ".webm" and supplied == "audio/webm":
        return supplied
    if extension == ".xlsx" and supplied in {"application/vnd.ms-excel", "application/zip"}:
        return expected
    return ""


def validate_upload(filename: str, content_type: str, size: int) -> str | None:
    content_type = normalize_upload_type(filename, content_type)
    limit = ALLOWED_UPLOAD_TYPES.get(content_type)
    if limit is None:
        return f"허용되지 않은 파일 형식입니다: {filename} ({content_type or '형식 없음'})"
    if size <= 0:
        return f"빈 파일은 제출할 수 없습니다: {filename}"
    if size > limit:
        return f"파일 용량 제한을 초과했습니다: {filename} ({limit // (1024 * 1024)}MB 이하)"
    return None


def safe_storage_name(filename: str) -> str:
    name = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", filename.strip())
    name = name.strip("._") or "upload.bin"
    return name[:120]


def _json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump(mode="json"))
    if dataclasses.is_dataclass(value):
        return _json_safe(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return str(value)


SIMULATION_ANSWER_KEYS = (
    "ragpbl_problem", "ragpbl_hypothesis", "ragpbl_action_plan",
    "ragpbl_evidence", "ragpbl_evaluation",
)

LEARNING_KEYS = (
        "hq_selected_unit",
        "hq_selected_scenario_id",
        "hq_unit_questions",
        "hq_scenarios_generated",
        "hq_submissions",
        "hq_reflections",
        "hq_xp",
        "hq_growth_log",
        "hq_earned_badges",
        "hq_rewarded_keys",
        "hq_final_submission_id",
        "ragpbl_questions",
        "ragpbl_discovery",
        "ragpbl_prior_knowledge",
        "ragpbl_selected_id",
        "ragpbl_review",
        "ragpbl_attempts",
        "ragpbl_source_mode",
        "ragpbl_review_source_mode",
        "ragpbl_saved_answer",
)


def build_learning_snapshot(identity: AppIdentity) -> dict[str, Any]:
    """Save the current unit only, with no account credentials or widget data."""
    from quest_engine import get_current_scenario_data, get_unit_questions_for_current

    unit = st.session_state["hq_selected_unit"]
    missions = get_current_scenario_data()["missions"]
    snapshot = {key: _json_safe(st.session_state.get(key)) for key in LEARNING_KEYS if key in st.session_state}
    snapshot["hq_unit_questions"] = _json_safe(get_unit_questions_for_current())
    for key in ("hq_submissions", "hq_reflections"):
        snapshot[key] = {m["id"]: snapshot[key][m["id"]] for m in missions if m["id"] in snapshot.get(key, {})}
    snapshot["mission_titles"] = {m["id"]: m["title"] for m in missions}
    if st.session_state.get("ragpbl_last_unit") != unit:
        snapshot = {key: value for key, value in snapshot.items() if not key.startswith("ragpbl_")}
    snapshot.update(snapshot.get("ragpbl_saved_answer") or {})
    snapshot.update(
        {
            "student_uid": identity.uid,
            "student_name": identity.name,
            "class_id": identity.class_id,
        }
    )
    if identity.uses_access_code:
        snapshot["login_method"] = "access_code"
    else:
        snapshot.update(student_email=identity.email, student_number=identity.student_number)
    return snapshot


class FirebaseBackend:
    """Small privileged backend. Every public method enforces application authorization."""

    def __init__(self, settings: FirebaseSettings):
        if not settings.configured:
            raise FirebaseConfigurationError("Firebase 서버 설정이 완성되지 않았습니다.")
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore, storage
        except ImportError as exc:
            raise FirebaseConfigurationError("firebase-admin 패키지가 설치되지 않았습니다.") from exc

        app_name = f"health-quest-{settings.project_id}"
        # Streamlit starts a separate script thread for each browser tab.
        # Both the lookup and creation must share the same initialization lock.
        with _firebase_app_init_lock:
            try:
                app = firebase_admin.get_app(app_name)
            except ValueError:
                try:
                    credential = credentials.Certificate(settings.service_account)
                except ValueError as exc:
                    raise FirebaseConfigurationError("서비스 계정 인증 정보 형식을 확인해 주세요.") from exc
                app = firebase_admin.initialize_app(
                    credential,
                    {"projectId": settings.project_id, "storageBucket": settings.storage_bucket},
                    name=app_name,
                )

        self._firestore = firestore
        self.settings = settings
        self.db = firestore.client(app=app)
        self.bucket = storage.bucket(app=app)

    def get_user_profile(self, uid: str) -> dict[str, Any] | None:
        if not uid:
            return None
        snapshot = self.db.collection("users").document(uid).get()
        return snapshot.to_dict() if snapshot.exists else None

    def issue_student_access_codes(self, teacher: AppIdentity, class_id: str, count: int) -> list[dict[str, str]]:
        require_role(teacher, "teacher")
        if self.settings.student_login_mode != "access_code" or class_id not in self.settings.class_ids:
            raise ValueError("학생 개별코드를 사용할 학급을 확인해 주세요.")
        if not 1 <= count <= MAX_CODES_PER_CLASS:
            raise ValueError(f"발급 수를 1~{MAX_CODES_PER_CLASS}개로 입력해 주세요.")
        now = datetime.now(timezone.utc)
        counter_ref = self.db.collection("student_access_counters").document(class_id)
        access_collection = self.db.collection("student_access")
        credentials = [(uuid.uuid4().hex, generate_access_code()) for _ in range(count)]

        @self._firestore.transactional
        def issue(transaction):
            counter = counter_ref.get(transaction=transaction).to_dict() or {}
            total = int(counter.get("issued", 0)) + count
            if total > MAX_CODES_PER_CLASS:
                raise ValueError(f"학급별로 최대 {MAX_CODES_PER_CLASS}명까지 발급할 수 있습니다. 남은 수를 확인해 주세요.")
            result = []
            for uid, code in credentials:
                transaction.create(access_collection.document(uid), {
                    "class_id": class_id,
                    "code_hash": code_digest(code),
                    "issued_at": now,
                    "expires_at": access_expiration(now),
                })
                result.append({"학급": class_id, "배부 표식": distribution_mark(uid), "접속코드": code})
            transaction.set(counter_ref, {"issued": total})
            return result

        return issue(self.db.transaction())

    def find_student_access(self, code_hash: str) -> tuple[str, dict[str, Any]] | None:
        from google.cloud.firestore_v1.base_query import FieldFilter

        if self.settings.student_login_mode != "access_code" or not re.fullmatch(r"[0-9a-f]{64}", code_hash):
            return None
        matches = self.db.collection("student_access").where(
            filter=FieldFilter("code_hash", "==", code_hash)
        ).limit(1).get()
        return (matches[0].id, matches[0].to_dict()) if matches else None

    def verify_student_access(self, uid: str, code_hash: str) -> dict[str, Any] | None:
        if self.settings.student_login_mode != "access_code" or not re.fullmatch(r"[0-9a-f]{32}", uid):
            return None
        credential = self.db.collection("student_access").document(uid).get().to_dict()
        if not credential or credential.get("code_hash") != code_hash:
            return None
        if credential["expires_at"] <= datetime.now(timezone.utc):
            return None
        return credential

    def list_access_roster(self, teacher: AppIdentity) -> list[dict[str, Any]]:
        require_role(teacher, "teacher")
        return [
            {"uid": doc.id, **{key: value for key, value in doc.to_dict().items() if key != "code_hash"}}
            for doc in self.db.collection("student_access").stream()
        ]

    def reissue_student_access_code(self, teacher: AppIdentity, uid: str) -> dict[str, str]:
        require_role(teacher, "teacher")
        if self.settings.student_login_mode != "access_code":
            raise ValueError("개별코드 방식이 꺼져 있습니다.")
        ref = self.db.collection("student_access").document(uid)
        code = generate_access_code()

        @self._firestore.transactional
        def reissue(transaction):
            credential = ref.get(transaction=transaction).to_dict()
            if not credential or credential["expires_at"] <= datetime.now(timezone.utc):
                raise ValueError("만료되었거나 존재하지 않는 발급번호입니다.")
            transaction.update(ref, {"code_hash": code_digest(code)})
            return {"학급": credential["class_id"], "배부 표식": distribution_mark(uid),
                    "접속코드": code}

        return reissue(self.db.transaction())

    def claim_student_alias(self, uid: str, code_hash: str, alias: str) -> bool:
        if alias not in FLOWER_ALIASES:
            raise ValueError("목록에서 꽃 별명을 선택해 주세요.")
        if not self.verify_student_access(uid, code_hash):
            raise AuthorizationError("접속코드를 다시 입력해 주세요.")
        credential_ref = self.db.collection("student_access").document(uid)
        profile_ref = self.db.collection("users").document(uid)

        @self._firestore.transactional
        def claim(transaction):
            credential = credential_ref.get(transaction=transaction).to_dict()
            if not credential or credential["code_hash"] != code_hash or credential["expires_at"] <= datetime.now(timezone.utc):
                raise AuthorizationError("접속코드를 다시 입력해 주세요.")
            if credential.get("alias"):
                return credential["alias"] == alias
            class_id = credential["class_id"]
            alias_ref = self.db.collection("student_aliases").document(f"{class_id}_{alias}")
            if alias_ref.get(transaction=transaction).exists:
                return False
            transaction.create(alias_ref, {"class_id": class_id, "alias": alias, "uid": uid})
            transaction.update(credential_ref, {"alias": alias})
            transaction.create(profile_ref, {
                "uid": uid, "role": "student", "display_name": alias,
                "class_id": class_id, "login_method": "access_code",
                "updated_at": self._firestore.SERVER_TIMESTAMP,
            })
            return True

        return claim(self.db.transaction())

    def _class_aliases(self, class_id: str) -> list[str]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        docs = self.db.collection("student_aliases").where(
            filter=FieldFilter("class_id", "==", class_id)
        ).stream()
        return sorted(doc.to_dict()["alias"] for doc in docs)

    def available_student_aliases(self, uid: str, code_hash: str) -> list[str]:
        credential = self.verify_student_access(uid, code_hash)
        if credential is None:
            raise AuthorizationError("접속코드를 다시 입력해 주세요.")
        occupied = set(self._class_aliases(credential["class_id"]))
        return [alias for alias in FLOWER_ALIASES if alias not in occupied]

    def _class_teams_document(self, class_id: str, login_mode: str):
        collection = "student_teams" if login_mode == "access_code" else "student_teams_google"
        return self.db.collection(collection).document(class_id)

    def list_class_teams(self, teacher: AppIdentity, class_id: str) -> dict[str, Any]:
        require_role(teacher, "teacher")
        ref = self._class_teams_document(class_id, self.settings.student_login_mode)
        return (ref.get().to_dict() or {}).get("teams", {})

    def save_class_team(self, teacher: AppIdentity, class_id: str, name: str, member_uids: list[str]) -> None:
        require_role(teacher, "teacher")
        if class_id not in self.settings.class_ids:
            raise ValueError("등록된 학급을 선택해 주세요.")
        if name not in TEAM_NAMES:
            raise ValueError("목록에서 모둠 이름을 선택해 주세요.")
        if not 2 <= len(member_uids) <= 6 or len(member_uids) != len(set(member_uids)):
            raise ValueError("모둠원은 서로 다른 학생 2~6명으로 지정해 주세요.")
        code_mode = self.settings.student_login_mode == "access_code"
        uid_pattern = r"[0-9a-f]{32}" if code_mode else r"[A-Za-z0-9_-]{1,128}"
        if not all(re.fullmatch(uid_pattern, uid) for uid in member_uids):
            raise ValueError("등록된 학생만 모둠에 넣을 수 있습니다.")
        team_ref = self._class_teams_document(class_id, self.settings.student_login_mode)
        collection = self.db.collection("student_access" if code_mode else "users")
        credentials = [collection.document(uid) for uid in member_uids]

        @self._firestore.transactional
        def save(transaction):
            teams = (team_ref.get(transaction=transaction).to_dict() or {}).get("teams", {})
            for existing_name, existing in teams.items():
                if existing_name != name and set(member_uids).intersection(existing["member_uids"]):
                    raise ValueError(f"이미 {existing_name} 모둠에 속한 학생이 있습니다. 기존 모둠 편성을 먼저 확인해 주세요.")
            profiles = {doc.id: doc.to_dict() or {} for doc in self.db.get_all(credentials, transaction=transaction)}
            members = [profiles.get(uid, {}) for uid in member_uids]
            if any(member.get("class_id") != class_id for member in members):
                raise ValueError("같은 학급으로 등록된 학생만 모둠에 넣을 수 있습니다.")
            if code_mode:
                now = datetime.now(timezone.utc)
                if any(not m.get("alias") or m["expires_at"] <= now for m in members):
                    raise ValueError("꽃 별명을 등록한 활성 학생만 모둠에 넣을 수 있습니다.")
                names = [member["alias"] for member in members]
            else:
                if any(m.get("role") != "student" or record_uses_access_code(m) or not m.get("display_name")
                       or not m.get("student_number") for m in members):
                    raise ValueError("학번과 이름을 등록한 Google 학생만 모둠에 넣을 수 있습니다.")
                names = [member["display_name"] for member in members]
            teams[name] = {"name": name, "member_uids": member_uids, "aliases": names}
            transaction.set(team_ref, {"teams": teams})

        save(self.db.transaction())

    def get_student_team(self, identity: AppIdentity) -> dict[str, Any] | None:
        require_role(identity, "student")
        if not identity.class_id:
            return None
        login_mode = "access_code" if identity.uses_access_code else "google"
        ref = self._class_teams_document(identity.class_id, login_mode)
        teams = (ref.get().to_dict() or {}).get("teams", {})
        return next((team for team in teams.values() if identity.uid in team["member_uids"]), None)

    def _team_final_document(self, identity: AppIdentity, unit_name: str, team_name: str):
        fields = ["final_simulation", identity.class_id, unit_name, team_name]
        if not identity.uses_access_code:
            fields.append("google")
        key = json.dumps(fields, ensure_ascii=False)
        submission_id = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        return self.db.collection("submissions").document(submission_id)

    def get_team_final_receipt(self, identity: AppIdentity, unit_name: str, team_name: str) -> str | None:
        require_role(identity, "student")
        doc = self._team_final_document(identity, unit_name, team_name)
        record = doc.get().to_dict()
        if record and identity.uid in record.get("team_member_uids", []):
            return doc.id
        return None

    def upsert_user_profile(self, identity: AppIdentity, profile: Mapping[str, Any]) -> None:
        require_role(identity, "student", "teacher", owner_uid=identity.uid)
        allowed = {
            "uid": identity.uid,
            "email": identity.email,
            "display_name": str(profile.get("display_name", identity.name)).strip()[:80],
            "role": identity.role,
            "class_id": str(profile.get("class_id", identity.class_id)).strip()[:30],
            "student_number": str(profile.get("student_number", identity.student_number)).strip()[:30],
            "updated_at": self._firestore.SERVER_TIMESTAMP,
        }
        self.db.collection("users").document(identity.uid).set(allowed, merge=True)

    def _learning_document(self, identity: AppIdentity, unit: str):
        unit_key = hashlib.sha256(unit.encode("utf-8")).hexdigest()[:20]
        return self.db.collection("learning_sessions").document(f"{identity.uid}_{unit_key}")

    def get_learning_snapshot(self, identity: AppIdentity, unit: str) -> dict[str, Any]:
        require_role(identity, "student")
        return self._learning_document(identity, unit).get().to_dict() or {}

    def save_learning_snapshot(self, identity: AppIdentity, snapshot: Mapping[str, Any]) -> None:
        require_role(identity, "student")
        payload = dict(_json_safe(snapshot))
        payload["student_uid"] = identity.uid
        payload["updated_at"] = self._firestore.SERVER_TIMESTAMP
        self._learning_document(identity, str(snapshot["hq_selected_unit"])).set(payload)

    def create_submission(
        self,
        identity: AppIdentity,
        metadata: Mapping[str, Any],
        files: list[tuple[str, str, bytes]],
    ) -> str:
        require_role(identity, "student", owner_uid=identity.uid)
        verified_files = []
        for filename, supplied_type, data in files:
            content_type = normalize_upload_type(filename, supplied_type)
            error = validate_upload(filename, supplied_type, len(data))
            if error:
                raise ValueError(error)
            verified_files.append((filename, content_type, data))
        reflection = str(metadata.get("reflection", "")).strip()
        submission_type = str(metadata.get("submission_type", "개인"))
        team_members = ""
        team_name = ""
        team = None
        if submission_type == "팀":
            team = self.get_student_team(identity)
            if team is None:
                raise ValueError("교사가 모둠을 편성한 뒤 팀 자료를 제출할 수 있습니다.")
            team_name = team["name"]
            team_members = ", ".join(team["aliases"])
        final_simulation = metadata.get("activity") == "final_simulation"
        if submission_type not in {"개인", "팀"} or (submission_type == "팀" and not team_members):
            raise ValueError("팀 제출에는 팀원 학번과 이름이 필요합니다.")
        if not reflection and not verified_files:
            raise ValueError("성찰 내용을 작성하거나 파일을 추가해 주세요.")
        if final_simulation and (
            submission_type != "팀" or not team_name or not reflection
            or not any(mime.startswith("audio/") for _, mime, _ in verified_files)
        ):
            raise ValueError("최종 제출에는 모둠명, 팀 답안과 음성 파일이 필요합니다.")
        unit_name = str(metadata.get("unit_name", ""))[:200]
        shared_final = bool(team and final_simulation)
        attempt_id = uuid.uuid4().hex
        if shared_final:
            doc = self._team_final_document(identity, unit_name, team_name)
            submission_id = doc.id
            previous = doc.get().to_dict()
            if previous:
                if identity.uid in previous.get("team_member_uids", []):
                    return submission_id
                raise ValueError("이 모둠의 해당 단원 제출이 이미 있습니다. 교사에게 확인해 주세요.")
            storage_id = f"{submission_id}/{attempt_id}"
        else:
            submission_id = storage_id = attempt_id
            doc = self.db.collection("submissions").document(submission_id)
        stored_files: list[dict[str, Any]] = []
        uploaded_blobs = []

        def discard_uploads():
            for blob in uploaded_blobs:
                try:
                    blob.delete()
                except Exception:
                    pass

        try:
            for index, (filename, content_type, data) in enumerate(verified_files, start=1):
                path = (
                    f"classes/{identity.class_id}/students/{identity.uid}/"
                    f"submissions/{storage_id}/{index:02d}_{safe_storage_name(filename)}"
                )
                blob = self.bucket.blob(path)
                blob.upload_from_string(data, content_type=content_type)
                uploaded_blobs.append(blob)
                stored_files.append({
                    "name": filename,
                    "content_type": content_type,
                    "size": len(data),
                    "storage_path": f"gs://{self.bucket.name}/{path}",
                })
        except Exception:
            discard_uploads()
            raise

        payload = {
            "submission_id": submission_id,
            "student_uid": identity.uid,
            "student_name": identity.name,
            "class_id": identity.class_id,
            "unit_name": unit_name,
            "submission_type": submission_type,
            "team_members": team_members[:500],
            "team_name": team_name[:80],
            "simulation_title": str(metadata.get("simulation_title", ""))[:200],
            "activity": "final_simulation" if final_simulation else "attachment",
            "reflection": reflection[:5000],
            "status": "submitted",
            "files": stored_files,
            "teacher_feedback": "",
            "rubric_score": None,
            "submitted_at": self._firestore.SERVER_TIMESTAMP,
            "updated_at": self._firestore.SERVER_TIMESTAMP,
        }
        if identity.uses_access_code:
            payload["login_method"] = "access_code"
        else:
            payload.update(student_email=identity.email, student_number=identity.student_number)
        if team:
            payload["team_member_uids"] = team["member_uids"]
        if shared_final:
            from google.api_core.exceptions import AlreadyExists

            try:
                doc.create(payload)
            except AlreadyExists:
                discard_uploads()
                if self.get_team_final_receipt(identity, unit_name, team_name) is None:
                    raise ValueError("이 모둠의 해당 단원 제출이 이미 있습니다. 교사에게 확인해 주세요.")
        else:
            doc.set(payload)
        return submission_id

    def list_student_submissions(self, identity: AppIdentity) -> list[dict[str, Any]]:
        require_role(identity, "student", owner_uid=identity.uid)
        from google.cloud.firestore_v1.base_query import FieldFilter

        collection = self.db.collection("submissions")
        own = collection.where(filter=FieldFilter("student_uid", "==", identity.uid)).stream()
        records = {item.id: item.to_dict() for item in own}
        shared = collection.where(filter=FieldFilter("team_member_uids", "array_contains", identity.uid)).stream()
        records.update({item.id: item.to_dict() for item in shared})
        return list(records.values())

    def list_teacher_dashboard(self, identity: AppIdentity) -> dict[str, list[dict[str, Any]]]:
        require_role(identity, "teacher")
        users = [item.to_dict() for item in self.db.collection("users").stream()]
        sessions = [item.to_dict() for item in self.db.collection("learning_sessions").stream()]
        submissions = [item.to_dict() for item in self.db.collection("submissions").stream()]
        return {"users": users, "sessions": sessions, "submissions": submissions}

    def save_teacher_feedback(
        self,
        identity: AppIdentity,
        submission_id: str,
        score: int,
        feedback: str,
        status: str,
        *,
        rubric_scores: Mapping[str, int] | None = None,
    ) -> None:
        require_role(identity, "teacher")
        if status not in {"reviewing", "revision_requested", "evaluated"}:
            raise ValueError("허용되지 않은 평가 상태입니다.")
        reference = self.db.collection("submissions").document(submission_id)
        rubric_details = None
        if rubric_scores is not None:
            saved = reference.get().to_dict()
            if not saved:
                raise ValueError("평가할 제출물을 찾을 수 없습니다.")
            rubric_id = rubric_for_submission(saved)
            scores = validate_rubric_scores(rubric_id, rubric_scores)
            score = sum(scores.values())
            rubric_details = {"id": rubric_id, "scores": scores}
        if not 0 <= score <= 100:
            raise ValueError("평가 점수는 0~100점이어야 합니다.")
        reference.update(
            {
                "rubric_score": int(score),
                "rubric_details": rubric_details,
                "teacher_feedback": feedback.strip()[:5000],
                "status": status,
                "teacher_uid": identity.uid,
                "evaluated_at": self._firestore.SERVER_TIMESTAMP,
                "updated_at": self._firestore.SERVER_TIMESTAMP,
            }
        )

    def signed_download_url(self, identity: AppIdentity, storage_path: str) -> str:
        require_role(identity, "teacher")
        prefix = f"gs://{self.bucket.name}/"
        if not storage_path.startswith(prefix):
            raise ValueError("잘못된 Storage 경로입니다.")
        blob = self.bucket.blob(storage_path.removeprefix(prefix))
        return blob.generate_signed_url(expiration=timedelta(minutes=15), method="GET")


def get_backend(settings: FirebaseSettings | None = None) -> FirebaseBackend:
    return FirebaseBackend(settings or load_firebase_settings())


def current_identity() -> AppIdentity | None:
    raw = st.session_state.get("hq_identity")
    if not isinstance(raw, Mapping):
        return None
    required = ("uid", "name", "role")
    if not all(raw.get(key) for key in required):
        return None
    return AppIdentity(
        uid=str(raw["uid"]),
        email=str(raw.get("email", "")),
        name=str(raw["name"]),
        role=str(raw["role"]),
        class_id=str(raw.get("class_id", "")),
        student_number=str(raw.get("student_number", "")),
        access_number=str(raw.get("access_number", "")),
        login_method=str(raw.get("login_method", "google")),
    )


def _user_value(key: str, default: str = "") -> str:
    try:
        value = getattr(st.user, key, None)
        if value is None and hasattr(st.user, "get"):
            value = st.user.get(key, default)
        return str(value or default)
    except Exception:
        return default


def sign_out_student_code() -> None:
    st.session_state.clear()


def _render_login_landing(settings: FirebaseSettings) -> None:
    st.markdown(
        """
        <style>
        .hq-login-hero {padding:2.2rem;border-radius:28px;background:linear-gradient(135deg,#f8f2e8,#e7f1ea);margin:1rem 0 1.4rem}
        .hq-login-hero h1 {color:#17324d;margin:0 0 .5rem;font-size:2.25rem}
        .hq-login-hero p {color:#55645d;margin:0}
        </style>
        <div class="hq-login-hero">
          <h1>HEALTH QUEST</h1>
          <p>간호 미션에서 모의상황실습까지 이어지는 참여형 보건간호 PBL</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    student_col, teacher_col = st.columns(2, gap="large")
    with student_col.container(border=True, height="stretch"):
        st.subheader("학생 로그인", icon=":material/school:")
        st.write("기초·중급·심화 미션, 모의상황실습, 수행평가 제출을 진행합니다.")
        if settings.student_login_mode == "access_code":
            with st.form("student_access_login", clear_on_submit=True):
                code = st.text_input("개별 접속코드", type="password", max_chars=35)
                submitted = st.form_submit_button("학생 로그인", type="primary", width="stretch")
            if submitted:
                submitted_hash = code_digest(code)
                try:
                    match = get_backend(settings).find_student_access(submitted_hash) if submitted_hash else None
                except Exception:
                    st.error("접속코드를 확인하지 못했습니다. 잠시 뒤 다시 시도해 주세요.")
                else:
                    if not match or match[1]["expires_at"] <= datetime.now(timezone.utc):
                        st.error("접속코드가 올바르지 않거나 사용 기간이 끝났습니다.")
                    else:
                        sign_out_student_code()
                        st.session_state["hq_access_credentials"] = (match[0], submitted_hash)
                        st.rerun()
            st.caption("선생님이 발급한 내 코드를 입력하세요. 처음 접속할 때 꽃 별명을 선택합니다.")
        elif st.button("Google 계정으로 학생 로그인", type="primary", use_container_width=True):
            st.login("google")
    with teacher_col.container(border=True, height="stretch"):
        st.subheader("교사 로그인", icon=":material/admin_panel_settings:")
        st.write("담당 학급의 진도, 제출 파일, 음성 기록과 평가 피드백을 확인합니다.")
        if st.button("Google 계정으로 교사 로그인", use_container_width=True):
            st.login("google")
    st.caption("교사 화면은 사전에 등록한 두 Google 계정만 접근할 수 있습니다.")


def require_authenticated_identity(settings: FirebaseSettings) -> AppIdentity | None:
    """Open a verified teacher or student session according to the deployment settings."""
    if not settings.enabled:
        st.session_state["hq_firebase_mode"] = False
        st.session_state.pop("hq_identity", None)
        return None

    st.session_state["hq_firebase_mode"] = True
    try:
        logged_in = bool(st.user.is_logged_in)
    except Exception:
        logged_in = False
    if not logged_in:
        if settings.student_login_mode != "access_code" and st.session_state.get("hq_access_credentials"):
            sign_out_student_code()
        if settings.student_login_mode == "access_code" and st.session_state.get("hq_access_credentials"):
            uid, code_hash = st.session_state["hq_access_credentials"]
            try:
                backend = get_backend(settings)
                credential = backend.verify_student_access(uid, code_hash)
            except Exception:
                st.error("학생 접속 정보를 확인하지 못했습니다. 잠시 뒤 다시 시도해 주세요.")
                st.stop()
            if credential:
                if not credential.get("alias"):
                    st.title("나의 꽃 별명 선택")
                    st.button("접속코드 로그아웃", on_click=sign_out_student_code)
                    try:
                        aliases = backend.available_student_aliases(uid, code_hash)
                    except Exception:
                        st.error("별명 목록을 불러오지 못했습니다. 다시 접속해 주세요.")
                        st.stop()
                    if not aliases:
                        st.warning("사용 가능한 꽃 별명이 없습니다. 선생님에게 알려 주세요.")
                        st.stop()
                    with st.form("claim_student_alias"):
                        alias = st.selectbox("꽃 별명", aliases)
                        chosen = st.form_submit_button("이 별명으로 시작", type="primary")
                    if chosen:
                        try:
                            if backend.claim_student_alias(uid, code_hash, alias):
                                st.rerun()
                            st.warning("방금 사용된 별명입니다. 다른 별명을 선택해 주세요.")
                        except Exception:
                            st.error("별명을 저장하지 못했습니다. 다시 시도해 주세요.")
                    st.stop()
                identity = AppIdentity(
                    uid=uid, email="", name=credential["alias"], role="student",
                    class_id=credential["class_id"], login_method="access_code",
                )
                st.session_state["hq_identity"] = identity.as_dict()
                st.session_state["hq_student_label"] = identity.name
                return identity
            sign_out_student_code()
            st.warning("접속코드가 교체됐거나 만료되었습니다. 사용 가능한 코드를 입력해 주세요.")
        else:
            st.session_state.pop("hq_identity", None)
        _render_login_landing(settings)
        st.stop()

    email = _user_value("email").strip().casefold()
    uid = _user_value("sub") or _user_value("id")
    name = _user_value("name") or email.split("@", 1)[0]
    if not email or not uid or _user_value("email_verified").casefold() != "true":
        st.error("Google 로그인 정보에서 이메일 또는 사용자 ID를 확인할 수 없습니다.")
        st.button("로그아웃", on_click=st.logout)
        st.stop()

    old_identity = current_identity()
    role = resolve_role(email, settings.teacher_emails)
    if role == "student" and settings.student_login_mode == "access_code":
        st.session_state.pop("hq_identity", None)
        st.warning("학생은 선생님에게 받은 개별 접속코드로 로그인하세요.")
        st.button("Google 로그아웃", on_click=st.logout)
        st.stop()
    if old_identity and (old_identity.uid != uid or old_identity.role != role):
        for key in list(st.session_state):
            del st.session_state[key]
    st.session_state["hq_firebase_mode"] = True
    provisional = AppIdentity(uid=uid, email=email, name=name, role=role)
    try:
        backend = get_backend(settings)
        profile = backend.get_user_profile(uid) or {}
    except Exception as exc:
        st.error("Firebase 서버 연결 설정을 확인해 주세요.")
        st.caption(f"오류 유형: {type(exc).__name__}")
        if isinstance(exc, FirebaseConfigurationError):
            st.caption(str(exc))
        if st.button("Firebase 연결 다시 시도"):
            st.rerun()
        st.stop()

    if role == "teacher":
        identity = provisional
        st.session_state.pop("hq_access_credentials", None)
        backend.upsert_user_profile(identity, {"display_name": name})
    else:
        class_id = str(profile.get("class_id", ""))
        student_number = str(profile.get("student_number", ""))
        display_name = str(profile.get("display_name", name))
        if not class_id or not student_number:
            st.header("학생 정보 등록", icon=":material/badge:")
            st.write("처음 한 번만 학급과 학번을 등록합니다. 이후 학습기록은 이 계정에 연결됩니다.")
            with st.form("student_profile_form"):
                entered_name = st.text_input("이름", value=display_name, max_chars=40)
                selected_class = st.selectbox("학급", settings.class_ids)
                entered_number = st.text_input("학번", placeholder="예: 2101", max_chars=30)
                saved = st.form_submit_button("학생 정보 저장", type="primary", use_container_width=True)
            if saved:
                if not entered_name.strip() or not entered_number.strip():
                    st.error("이름과 학번을 입력해 주세요.")
                else:
                    identity = AppIdentity(
                        uid=uid,
                        email=email,
                        name=entered_name.strip(),
                        role="student",
                        class_id=selected_class,
                        student_number=entered_number.strip(),
                    )
                    backend.upsert_user_profile(identity, identity.as_dict())
                    st.session_state["hq_identity"] = identity.as_dict()
                    st.rerun()
            st.stop()
        identity = AppIdentity(
            uid=uid,
            email=email,
            name=display_name,
            role="student",
            class_id=class_id,
            student_number=student_number,
        )

    st.session_state["hq_identity"] = identity.as_dict()
    if identity.role == "student":
        st.session_state["hq_student_label"] = f"{identity.student_number} {identity.name}".strip()
    return identity


def persist_current_learning_state(settings: FirebaseSettings, identity: AppIdentity | None) -> None:
    if not settings.enabled or identity is None or identity.role != "student":
        return
    snapshot = build_learning_snapshot(identity)
    if not any(snapshot.get(key) for key in ("hq_unit_questions", "hq_submissions", "ragpbl_discovery")):
        return
    if snapshot["hq_selected_unit"] != st.session_state.get("hq_loaded_unit"):
        return
    serialized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if st.session_state.get("hq_last_firebase_snapshot_hash") == digest:
        return
    try:
        get_backend(settings).save_learning_snapshot(identity, snapshot)
        st.session_state["hq_last_firebase_snapshot_hash"] = digest
        st.session_state["hq_firebase_sync_error"] = ""
    except Exception as exc:
        st.session_state["hq_firebase_sync_error"] = type(exc).__name__


def persist_learning_now() -> None:
    if st.session_state.get("hq_firebase_mode"):
        persist_current_learning_state(load_firebase_settings(), current_identity())


def restore_learning_unit(settings: FirebaseSettings, identity: AppIdentity) -> None:
    from rag_pbl_single_agent import DiscoveryResult, PBLReview

    unit = st.session_state["hq_selected_unit"]
    if st.session_state.get("hq_loaded_unit") == unit:
        return
    try:
        record = get_backend(settings).get_learning_snapshot(identity, unit)
    except Exception as exc:
        st.session_state["hq_firebase_sync_error"] = type(exc).__name__
        st.error("저장된 학습기록을 불러오지 못했습니다. 연결이 복구되면 다시 시도해 주세요.")
        if st.button("학습기록 다시 불러오기"):
            st.rerun()
        st.stop()

    for key in list(st.session_state):
        if key.startswith(("ragpbl_", "rat_", "radio_")):
            del st.session_state[key]
    for key in ("hq_submissions", "hq_reflections", "hq_scenarios_generated"):
        st.session_state[key] = record.get(key) or {}
    for key in ("hq_unit_questions", "hq_growth_log", "hq_earned_badges", "hq_rewarded_keys"):
        st.session_state[key] = record.get(key) or []
    st.session_state["hq_xp"] = record.get("hq_xp") or 0
    st.session_state["hq_final_submission_id"] = record.get("hq_final_submission_id") or ""
    if record.get("hq_selected_scenario_id"):
        st.session_state["hq_selected_scenario_id"] = record["hq_selected_scenario_id"]
    if record.get("ragpbl_discovery"):
        st.session_state["ragpbl_last_unit"] = unit
        for key in LEARNING_KEYS:
            if key.startswith("ragpbl_") and key in record:
                st.session_state[key] = record[key]
        st.session_state["ragpbl_discovery"] = DiscoveryResult.model_validate(record["ragpbl_discovery"])
        if record.get("ragpbl_review"):
            st.session_state["ragpbl_review"] = PBLReview.model_validate(record["ragpbl_review"])
        st.session_state["ragpbl_saved_answer"] = {
            key: record[key] for key in SIMULATION_ANSWER_KEYS if key in record
        }
    st.session_state["hq_loaded_unit"] = unit
    st.session_state["hq_firebase_sync_error"] = ""
