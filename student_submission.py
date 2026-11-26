"""Student file, image, audio, and video submission portal."""

import streamlit as st

from evaluation_rubrics import status_label

from firebase_integration import (
    current_identity,
    get_backend,
    load_firebase_settings,
    validate_upload,
)
from submission_sample import alias_worksheet, sample_workbook


st.set_page_config(page_title="HEALTH QUEST — 수행평가 제출", page_icon="📤", layout="wide")
settings = load_firebase_settings()
identity = current_identity()

if not settings.enabled or identity is None:
    st.error("Firebase 로그인 후 사용할 수 있는 페이지입니다.")
    st.stop()
if identity.role != "student":
    st.error("학생 계정만 수행평가를 제출할 수 있습니다.")
    st.stop()

def show_receipts(focused_id: str = "") -> None:
    try:
        records = get_backend(settings).list_student_submissions(identity)
    except Exception as exc:
        st.error(f"제출 기록을 불러오지 못했습니다. 다시 시도해 주세요. ({type(exc).__name__})")
        return
    if focused_id:
        records = [item for item in records if item.get("submission_id") == focused_id]
        if not records:
            st.warning("이 계정에서 해당 제출을 확인할 수 없습니다.")
    for item in sorted(records, key=lambda value: str(value.get("submitted_at", "")), reverse=True):
        with st.container(border=True):
            st.text(f"{item.get('unit_name') or '단원 미입력'} · {status_label(item.get('status', 'submitted'))}")
            if item.get("activity") == "final_simulation":
                st.badge("모의상황실습 최종 제출", color="green")
            if item.get("team_name"):
                st.text(f"{item['team_name']} · {item.get('team_members', '')}")
            if item.get("reflection") and (focused_id or item.get("team_member_uids")):
                with st.expander("모둠이 제출한 답안" if item.get("team_name") else "내가 제출한 답안",
                                 expanded=bool(focused_id)):
                    st.text(item["reflection"])
            submission_id = str(item.get("submission_id", ""))
            st.caption(f"제출번호 {submission_id[:8]}")
            if not focused_id and submission_id:
                st.button("내 제출 확인", key=f"open_receipt_{submission_id}",
                          on_click=lambda receipt=submission_id: st.session_state.update(hq_receipt_focus=receipt))
            for attached in item.get("files", []):
                st.text(attached.get("name", "첨부 파일"))
            if item.get("rubric_score") is not None:
                st.caption(f"루브릭 점수 {item['rubric_score']}/100")
            st.caption(f"교사 피드백: {item.get('teacher_feedback') or '아직 등록되지 않았습니다.'}")
    if not records and not focused_id:
        st.caption("아직 Firebase에 저장된 제출 기록이 없습니다.")


def clear_receipt_focus() -> None:
    st.session_state.pop("hq_receipt_focus", None)
    st.query_params.pop("receipt", None)


def close_team_recording_guide() -> None:
    st.session_state.pop("hq_team_recording_guide", None)


def open_team_recording_guide() -> None:
    st.session_state["hq_team_recording_guide"] = True


def warn_when_team_selected() -> None:
    if st.session_state.get("hq_attachment_submission_type") == "팀":
        open_team_recording_guide()


@st.dialog("모둠 최종 답안 녹음 안내", on_dismiss=close_team_recording_guide)
def show_team_recording_guide() -> None:
    st.write("토의 후 합의한 모둠 최종 답안을 함께 음성으로 녹음해 제출하세요.")
    st.write("개인 모의상황실습을 마친 모둠원 한 명이 **모의상황실습 마지막 화면**에서 공동 답안을 적고 녹음한 뒤 **모둠 답안과 음성을 교사에게 제출**을 누르면 됩니다.")
    if st.button("모의상황실습으로 이동", type="primary"):
        close_team_recording_guide()
        st.switch_page("app_rag_pbl.py")
    if st.button("이 화면에서 자료 첨부 계속"):
        close_team_recording_guide()
        st.rerun()


focused_receipt = st.session_state.get("hq_receipt_focus", "") or st.query_params.get("receipt", "")
if focused_receipt:
    st.title("제출 내용 확인", anchor=False)
    st.button("제출 화면과 전체 기록으로 돌아가기", on_click=clear_receipt_focus)
    if result := st.session_state.pop("hq_receipt_success", ""):
        st.success(f"교사 제출함에 저장했습니다. 제출번호 {result[:8]}")
    show_receipts(focused_receipt)
    st.stop()

st.title("수행평가 자료 제출", anchor=False)
st.caption(identity.name if identity.uses_access_code else f"{identity.class_id} · {identity.student_number} {identity.name}")
st.info("기존 Excel 학습지와 개별 파일은 이 화면에서 제출하세요. 모둠 최종 수행평가는 모의상황실습 마지막 화면에서 제출합니다.")
st.info("실제 환자의 얼굴·이름·연락처·진료정보가 포함된 파일은 제출하지 마세요.", icon=":material/privacy_tip:")
st.download_button(
    "제출 테스트용 Excel 받기", sample_workbook(),
    file_name="HEALTH_QUEST_제출테스트.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    icon=":material/download:", on_click="ignore",
)
st.caption("다운로드한 샘플을 아래 첨부란에 직접 올려야 교사 제출함에 등록됩니다.")
assigned_team = None
if identity.uses_access_code:
    st.caption("새 학습지는 아래 별명 양식으로 시작하세요.")
try:
    assigned_team = get_backend(settings).get_student_team(identity)
except Exception:
    st.warning("모둠 편성을 가져오지 못했습니다. 팀 자료를 제출하려면 다시 접속해 주세요.")
if assigned_team:
    st.info(f"내 모둠 · {assigned_team['name']} — {', '.join(assigned_team['aliases'])}")
    st.caption("개인 모의상황실습을 마친 모둠원 한 명이 최종 화면에서 공동 답안과 음성을 제출합니다. 제출 기록과 교사 평가는 모둠원 모두가 여기서 확인할 수 있습니다.")
else:
    st.caption("교사가 모둠을 편성하면 여기에 모둠 이름과 모둠원이 표시됩니다. 개인 자료는 지금 제출할 수 있습니다.")
if identity.uses_access_code:
    st.download_button(
        "개인·모둠 별명 학습지 Excel 받기",
        alias_worksheet(identity.name, assigned_team["name"] if assigned_team else ""),
        file_name="HEALTH_QUEST_별명학습지.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/download:", on_click="ignore",
    )

available_types = ["개인", "팀"] if assigned_team else ["개인"]
submission_type = st.radio(
    "제출 유형", available_types, horizontal=True, key="hq_attachment_submission_type",
    on_change=warn_when_team_selected,
)
if assigned_team:
    st.button("모둠 최종 녹음 안내", on_click=open_team_recording_guide)
    if st.session_state.get("hq_team_recording_guide"):
        show_team_recording_guide()
if submission_type == "팀":
    st.caption("이 양식은 팀 참고자료 제출용입니다. 모둠 최종 공동 답안과 녹음은 ‘모의상황실습’의 마지막 화면에서 제출합니다.")

with st.form("firebase_submission_form", clear_on_submit=False):
    unit_name = st.text_input(
        "단원 또는 모의상황 이름",
        value=str(st.session_state.get("hq_selected_unit", "")),
        max_chars=200,
    )
    reflection = st.text_area(
        "판단 근거와 성찰",
        placeholder="모의상황에서 어떤 단서를 근거로 판단했고 다음에는 무엇을 보완할지 작성하세요.",
        height=160,
        max_chars=5000,
    )
    files = st.file_uploader(
        "Excel·PDF·문서·텍스트 파일·이미지·음성·영상",
        type=["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg", "mp3", "wav", "webm", "mp4"],
        accept_multiple_files=True,
        help="텍스트 1MB, 문서·이미지 20MB, 음성 25MB, 영상 100MB 이하",
    )
    recorded = st.audio_input("마이크로 개인 또는 팀 보고를 녹음하세요")
    submitted = st.form_submit_button("교사에게 안전하게 제출", type="primary", use_container_width=True)

if submitted:
    upload_items: list[tuple[str, str, bytes]] = []
    errors: list[str] = []
    for uploaded in files or []:
        data = uploaded.getvalue()
        content_type = uploaded.type or ""
        if error := validate_upload(uploaded.name, content_type, len(data)):
            errors.append(error)
        else:
            upload_items.append((uploaded.name, content_type, data))
    if recorded is not None:
        data = recorded.getvalue()
        content_type = recorded.type or "audio/wav"
        if error := validate_upload("recording.wav", content_type, len(data)):
            errors.append(error)
        else:
            upload_items.append(("recording.wav", content_type, data))

    if not reflection.strip() and not upload_items:
        errors.append("성찰 내용을 작성하거나 제출 파일을 추가해 주세요.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        try:
            with st.spinner("Firebase Storage와 교사 제출함에 저장하는 중..."):
                submission_id = get_backend(settings).create_submission(
                    identity,
                    {
                        "unit_name": unit_name,
                        "submission_type": submission_type,
                        "reflection": reflection,
                    },
                    upload_items,
                )
            st.session_state["hq_receipt_focus"] = submission_id
            st.session_state["hq_receipt_success"] = submission_id
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error("제출 중 오류가 발생했습니다. 파일은 공개되지 않았습니다.")
            st.caption(f"오류 유형: {type(exc).__name__}")

st.divider()
st.subheader("나의 최근 제출 기록", anchor=False)
show_receipts()
