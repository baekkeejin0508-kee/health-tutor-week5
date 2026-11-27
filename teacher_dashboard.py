"""Authenticated teacher-only dashboard for Firebase classroom records."""

import csv
from datetime import datetime, timezone
from inspect import Parameter, signature
from io import BytesIO, StringIO
from time import monotonic

import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from evaluation_rubrics import RUBRICS, SCORE_LEVELS, rubric_for_submission, status_label
from firebase_integration import current_identity, get_backend, load_firebase_settings
from quest_data import UNIT_CATALOG
from student_access import MAX_CODES_PER_CLASS, TEAM_NAMES, code_digest, distribution_mark, record_uses_access_code


ACCESS_CODE_COLUMNS = ("학급", "배부 표식", "접속코드")


def access_codes_workbook(codes):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "학생 접속코드"
    sheet.append(ACCESS_CODE_COLUMNS)
    for row in codes:
        sheet.append([row[column] for column in ACCESS_CODE_COLUMNS])
        for cell in sheet[sheet.max_row]:
            cell.data_type = "s"
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="203864")
    for column, width in zip("ABC", (12, 22, 32)):
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def read_access_codes_csv(data):
    if len(data) > 65536:
        raise ValueError("접속코드 CSV 파일 크기를 확인해 주세요.")
    try:
        content = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = data.decode("cp949")
    reader = csv.DictReader(StringIO(content, newline=""), strict=True)
    if reader.fieldnames != list(ACCESS_CODE_COLUMNS):
        raise ValueError("‘학급’, ‘배부 표식’, ‘접속코드’ 열이 있는 발급용 CSV를 선택해 주세요.")
    rows = list(reader)
    if not rows or any(None in row or not code_digest(row["접속코드"] or "") for row in rows):
        raise ValueError("CSV에서 유효한 형식의 접속코드를 확인해 주세요.")
    return rows


st.set_page_config(page_title="HEALTH QUEST — 교사 대시보드", page_icon="📋", layout="wide")
settings = load_firebase_settings()
identity = current_identity()

if not settings.enabled or identity is None or identity.role != "teacher":
    st.error("등록된 교사 계정만 접근할 수 있습니다.")
    st.stop()

st.title("교사 평가 대시보드", anchor=False)
teacher_count = len(settings.teacher_emails)
teacher_scope = f"등록된 교사 계정 {teacher_count}개" if teacher_count else "등록된 교사 계정"
st.caption(
    f"현재 로그인: {identity.name} · {teacher_scope}가 "
    f"{len(settings.class_ids)}개 반의 동일한 제출함을 공동으로 확인·평가합니다."
)
if saved_receipt := st.session_state.pop("hq_rubric_saved", ""):
    st.session_state.pop(f"manual_status_{saved_receipt}", None)
    st.session_state.pop(f"manual_feedback_{saved_receipt}", None)
    st.success("항목별 루브릭 점수와 교사 평가를 저장했습니다.")

try:
    backend = get_backend(settings)
    data = backend.list_teacher_dashboard(identity)
except Exception as exc:
    st.error("Firebase 자료를 불러오지 못했습니다.")
    st.caption(f"오류 유형: {type(exc).__name__}")
    st.stop()

feedback_parameters = signature(backend.save_teacher_feedback).parameters
rubric_save_available = "rubric_scores" in feedback_parameters or any(
    parameter.kind is Parameter.VAR_KEYWORD for parameter in feedback_parameters.values()
)
restart_message = "이 서버가 이전 평가 코드를 사용 중입니다. 입력한 점수와 피드백을 메모한 뒤 Streamlit 서버를 재시작해 주세요."
if not rubric_save_available:
    st.warning(restart_message)


REVIEW_STATUSES = ("reviewing", "revision_requested", "evaluated")


def evaluation_status_selector(item, key):
    current = item.get("status")
    return st.selectbox(
        "평가 상태", REVIEW_STATUSES, key=key, format_func=status_label,
        index=REVIEW_STATUSES.index(current) if current in REVIEW_STATUSES else 0,
    )


def evaluator_label(item):
    """Return a human-readable last evaluator without exposing an internal UID."""
    name = str(item.get("teacher_name") or "").strip()
    email = str(item.get("teacher_email") or "").strip()
    if name and email:
        return f"{name} ({email})"
    return name or email


def render_attachment(item, index, file_info, *, in_dialog=False):
    submission_id = item["submission_id"]
    storage_path = str(file_info.get("storage_path", ""))
    content_type = str(file_info.get("content_type", ""))
    st.text(str(file_info.get("name", "첨부 파일")))
    url_key = f"signed_preview_{submission_id}_{index}"
    location = "rubric" if in_dialog else "list"
    if storage_path and st.button("첨부파일 열기 · 15분", key=f"signed_{location}_{submission_id}_{index}"):
        try:
            url = backend.signed_download_url(identity, storage_path)
            st.session_state[url_key] = (url, monotonic() + 890)
        except Exception as exc:
            st.error(f"미리보기 링크 생성 실패: {type(exc).__name__}")
    preview = st.session_state.get(url_key)
    if preview and monotonic() < preview[1]:
        url = preview[0]
        if content_type.startswith("audio/"):
            st.audio(url)
        elif content_type.startswith("video/"):
            st.video(url)
        elif content_type.startswith("image/"):
            st.image(url)
        st.link_button("원본 파일 열기", url)
    elif preview:
        st.session_state.pop(url_key, None)
        st.caption("열람 시간이 지났습니다. 첨부파일 열기 버튼을 다시 누르세요.")


def close_rubric_dialog():
    st.session_state.pop("hq_active_rubric", None)


@st.dialog("수업 내용별 루브릭 평가", width="large", on_dismiss=close_rubric_dialog)
def show_rubric_dialog(item):
    submission_id = item["submission_id"]
    rubric_id = rubric_for_submission(item)
    title, criteria = RUBRICS[rubric_id]
    unit_name = item.get("unit_name") or "단원 미입력"
    st.subheader(title)
    st.text(f"{unit_name} · 제출번호 {submission_id[:8]}")
    if evaluator := evaluator_label(item):
        st.caption(f"마지막 평가 교사: {evaluator}")
    mission_objectives = list(dict.fromkeys(
        (mission.get("level_label", ""), mission["learning_objective"])
        for scenario in UNIT_CATALOG.get(unit_name, {}).get("scenarios", [])
        for mission in scenario.get("missions", [])
        if mission.get("learning_objective")
    ))
    if mission_objectives:
        with st.expander("이 단원의 학습 목표", expanded=True):
            for level, objective in mission_objectives:
                st.markdown(f"- {level + ' · ' if level else ''}{objective}")
    if item.get("reflection") or item.get("files"):
        with st.expander("답안과 첨부파일 확인"):
            if item.get("reflection"):
                st.text(item["reflection"])
            for index, file_info in enumerate(item.get("files", [])):
                render_attachment(item, index, file_info, in_dialog=True)

    details = item.get("rubric_details") or {}
    saved = details.get("scores", {}) if details.get("id") == rubric_id else {}
    levels = list(SCORE_LEVELS)
    st.caption("항목당 25점, 총 100점입니다. 제출물에서 확인한 근거에 맞는 수준을 각 항목에서 선택하세요.")
    scores = {}
    with st.form(f"rubric_form_{submission_id}"):
        for key, label, evidence in criteria:
            previous = saved.get(key)
            st.caption(f"{label} · 만점 기준: {evidence}")
            scores[key] = st.selectbox(
                label, levels, index=levels.index(previous) if previous in levels else None,
                placeholder="점수 수준 선택", format_func=lambda value: f"{value}점 · {SCORE_LEVELS[value]}",
            )
        feedback = st.text_area("교사 피드백", value=str(item.get("teacher_feedback") or ""), max_chars=5000)
        status = evaluation_status_selector(item, f"rubric_status_{submission_id}")
        submit = st.form_submit_button(
            "항목별 점수와 평가 저장", type="primary", disabled=not rubric_save_available,
        )
    if not rubric_save_available:
        st.warning(restart_message)
    if submit:
        if any(value is None for value in scores.values()):
            st.warning("네 항목의 점수 수준을 모두 선택해 주세요.")
            return
        try:
            backend.save_teacher_feedback(identity, submission_id, sum(scores.values()), feedback, status,
                                          rubric_scores=scores)
        except Exception as exc:
            st.error(f"루브릭 평가를 저장하지 못했습니다. ({type(exc).__name__})")
        else:
            st.session_state["hq_rubric_saved"] = submission_id
            close_rubric_dialog()
            st.rerun()


code_mode = settings.student_login_mode == "access_code"
students = [item for item in data["users"] if item.get("role") == "student"
            and record_uses_access_code(item) == code_mode]
submissions = [item for item in data["submissions"] if record_uses_access_code(item) == code_mode]
sessions = [item for item in data["sessions"] if record_uses_access_code(item) == code_mode]
st.caption("학생 로그인 방식 · 개별 접속코드" if code_mode else "학생 로그인 방식 · Google")

if code_mode:
    with st.expander("저장한 접속코드 CSV를 엑셀로 변환"):
        st.caption("이미 받은 접속코드 CSV를 올려 엑셀 파일로 저장하세요. 학생 코드는 그대로 사용할 수 있습니다.")
        uploaded_codes = st.file_uploader("발급용 접속코드 CSV", type=["csv"])
        if uploaded_codes is not None:
            try:
                saved_codes = read_access_codes_csv(uploaded_codes.getvalue())
            except (UnicodeError, csv.Error):
                st.error("CSV 파일을 읽지 못했습니다. 앱에서 다운로드한 발급용 CSV를 선택해 주세요.")
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.download_button(
                    f"기존 접속코드 {len(saved_codes)}개 엑셀(.xlsx) 다운로드",
                    access_codes_workbook(saved_codes),
                    file_name="HEALTH_QUEST_개별접속코드.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    on_click="ignore",
                )
    with st.expander("학생 접속코드 발급 및 꽃 별명 확인"):
        st.caption("학생에게는 접속코드만 전달하세요. 배부 표식은 교사가 명단과 접속코드를 대조할 때 사용합니다. 실명과 표식의 대응은 학교 내부 명부에만 기록하세요.")
        with st.form("issue_student_codes"):
            class_id = st.selectbox("발급할 학급", settings.class_ids)
            count = st.number_input("발급 수", min_value=1, max_value=MAX_CODES_PER_CLASS, value=1,
                                    help=f"학급별 최대 {MAX_CODES_PER_CLASS}명까지 발급할 수 있습니다.")
            issue = st.form_submit_button("개별 접속코드 일괄 발급", type="primary")
        if issue:
            try:
                st.session_state["issued_student_codes"] = backend.issue_student_access_codes(
                    identity, class_id, int(count)
                )
            except ValueError as exc:
                st.error(str(exc))
            except Exception:
                st.error("접속코드를 발급하지 못했습니다. Firebase 연결을 확인하고 다시 시도해 주세요.")

        try:
            roster = sorted(backend.list_access_roster(identity),
                            key=lambda item: (item["class_id"], distribution_mark(item["uid"])))
        except Exception:
            roster = []
            st.error("배부 표식과 별명 목록을 불러오지 못했습니다.")
        if roster:
            st.dataframe([
                {"학급": row["class_id"], "배부 표식": distribution_mark(row["uid"]),
                 "꽃 별명": row.get("alias") or "선택 전",
                 "만료일": row["expires_at"].date().isoformat()}
                for row in roster
            ], hide_index=True)
            roster_by_uid = {row["uid"]: row for row in roster}
            now = datetime.now(timezone.utc)
            active_uids = [
                row["uid"] for row in roster
                if row["class_id"] in settings.class_ids and row["expires_at"] > now
            ]
            if active_uids:
                with st.form("replace_all_student_codes"):
                    st.subheader("전체 학생 접속코드 재발급")
                    st.caption(
                        f"기존 학생 {len(active_uids)}명의 새 접속코드를 엑셀 또는 CSV 파일로 받습니다. "
                        "배부 표식, 별명, 학습 기록과 제출물은 유지됩니다."
                    )
                    confirm_all = st.checkbox("대상 학생 모두의 기존 코드가 즉시 중단됨을 확인했습니다.")
                    replace_all = st.form_submit_button(f"{len(active_uids)}명 접속코드 재발급")
                if replace_all and not confirm_all:
                    st.warning("전체 학생의 기존 코드 중단을 확인해 주세요.")
                elif replace_all:
                    try:
                        st.session_state["issued_student_codes"] = backend.reissue_student_access_codes(
                            identity, active_uids,
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("전체 코드를 재발급하지 못했습니다. Firebase 연결을 확인해 주세요.")
                    else:
                        st.success("새 코드가 준비됐습니다. 아래에서 엑셀 또는 CSV 파일을 다운로드하세요.")
            with st.form("replace_student_code"):
                selected_uid = st.selectbox(
                    "코드를 분실한 학생", list(roster_by_uid),
                    format_func=lambda uid: (
                        f"{roster_by_uid[uid]['class_id']} · {roster_by_uid[uid].get('alias') or '별명 선택 전'} · {distribution_mark(uid)}"
                    ),
                )
                confirmed = st.checkbox("기존 코드 사용이 즉시 중단됨을 확인했습니다.")
                replace = st.form_submit_button("접속코드 재발급")
            if replace and not confirmed:
                st.warning("기존 코드 중단을 확인해 주세요.")
            elif replace:
                try:
                    st.session_state["issued_student_codes"] = [backend.reissue_student_access_code(identity, selected_uid)]
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("코드를 재발급하지 못했습니다.")
        if codes := st.session_state.get("issued_student_codes"):
            st.warning("접속코드 파일을 지금 저장하세요. ‘접속코드’ 열의 값만 각 학생에게 개별 전달하세요.")
            st.table(codes)
            st.download_button(
                f"접속코드 {len(codes)}개 엑셀(.xlsx) 다운로드",
                access_codes_workbook(codes),
                file_name="HEALTH_QUEST_개별접속코드.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                on_click="ignore",
            )
            buffer = StringIO()
            writer = csv.DictWriter(buffer, fieldnames=ACCESS_CODE_COLUMNS)
            writer.writeheader()
            writer.writerows(codes)
            st.download_button(f"접속코드 {len(codes)}개 CSV 다운로드", buffer.getvalue().encode("utf-8-sig"),
                               file_name="HEALTH_QUEST_개별접속코드.csv", mime="text/csv")
            if st.button("코드 표시 닫기"):
                st.session_state.pop("issued_student_codes", None)
                st.rerun()
with st.expander("모둠 편성 관리"):
    st.caption("학생이 등록을 마치면 같은 반에서 2~6명을 묶으세요. 편성은 학생 화면에 자동으로 표시됩니다.")
    team_class = st.selectbox("모둠을 편성할 학급", settings.class_ids)
    if code_mode:
        class_students = {row["uid"]: row["alias"] for row in roster
                          if row["class_id"] == team_class and row.get("alias")}
    else:
        class_students = {row["uid"]: f"{row['student_number']} {row['display_name']}" for row in students
                          if row.get("class_id") == team_class and row.get("uid")
                          and row.get("student_number") and row.get("display_name")}
    try:
        teams = backend.list_class_teams(identity, team_class)
    except Exception:
        st.error("모둠 명단을 가져오지 못했습니다.")
    else:
        if teams:
            st.dataframe([
                {"모둠 이름": team["name"], "모둠원": ", ".join(team["aliases"])}
                for team in teams.values()
            ], hide_index=True)
        if len(class_students) < 2:
            st.info("이 학급에 등록한 학생이 2명 이상이면 모둠을 만들 수 있습니다.")
        else:
            team_name = st.selectbox("모둠 이름 선택", TEAM_NAMES)
            assigned = {uid for name, team in teams.items() if name != team_name for uid in team["member_uids"]}
            eligible = [uid for uid in class_students if uid not in assigned]
            current = teams.get(team_name, {}).get("member_uids", [])
            with st.form(f"save_team_{team_class}_{team_name}"):
                selected = st.multiselect(
                    "모둠원 꽃 별명" if code_mode else "모둠원 학번·이름", eligible,
                    default=[uid for uid in current if uid in eligible],
                    format_func=class_students.__getitem__, max_selections=6,
                )
                save_team = st.form_submit_button("모둠 편성 저장", type="primary")
            if save_team:
                try:
                    backend.save_class_team(identity, team_class, team_name, selected)
                    st.toast(f"{team_name} 모둠을 저장했습니다.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("모둠 편성을 저장하지 못했습니다.")

metric_cols = st.columns(4)
metric_cols[0].metric("등록 학생", len(students), border=True)
metric_cols[1].metric("학습 기록", len(sessions), border=True)
metric_cols[2].metric("수행평가 제출", len(submissions), border=True)
metric_cols[3].metric(
    "평가 대기",
    sum(1 for item in submissions if item.get("status") in {"submitted", "reviewing"}),
    border=True,
)

filter_cols = st.columns(3)
selected_class = filter_cols[0].selectbox("학급", ["전체", *settings.class_ids])
selected_status = filter_cols[1].selectbox(
    "상태", ["전체", "submitted", *REVIEW_STATUSES], format_func=status_label,
)
search_name = filter_cols[2].text_input(
    "꽃 별명 검색" if code_mode else "학생 이름·학번 검색"
)

def matches_student(item, name_field):
    identity_text = (
        f"{item.get(name_field, '')} {'' if code_mode else item.get('student_number', '')} "
        f"{item.get('team_name', '')} {item.get('team_members', '')}"
    )
    return (
        (selected_class == "전체" or item.get("class_id") == selected_class)
        and search_name.strip().casefold() in identity_text.casefold()
    )


with st.expander("등록 학생과 개인 성장기록"):
    filtered_students = [student for student in students if matches_student(student, "display_name")]
    if filtered_students:
        st.dataframe([
            {"학급": s.get("class_id"),
             **({} if code_mode else {"학번": s.get("student_number")}),
             ("별명" if code_mode else "이름"): s.get("display_name"),
             "학습 단원 수": sum(record.get("student_uid") == s.get("uid") for record in sessions)}
            for s in filtered_students
        ], hide_index=True)
    else:
        st.info("조건에 맞는 등록 학생이 없습니다.")
    filtered_sessions = [session for session in sessions if matches_student(session, "student_name")]
    for record in sorted(filtered_sessions, key=lambda item: str(item.get("updated_at", "")), reverse=True):
        student_number = "" if code_mode else f"{record.get('student_number', '')} "
        label = f"{record.get('class_id', '')} · {student_number}{record.get('student_name', '')} · {record.get('hq_selected_unit', '')}"
        with st.expander(label):
            answers = record.get("hq_submissions") or {}
            for mission_id, result in answers.items():
                st.caption(record.get("mission_titles", {}).get(mission_id, mission_id))
                st.text(result.get("rationale", ""))
                st.caption("통과" if result.get("is_correct") else "재도전")
                if reflection := (record.get("hq_reflections") or {}).get(mission_id):
                    st.text(reflection)
            if not answers:
                st.caption("저장된 단계별 서술이 아직 없습니다.")
            if record.get("ragpbl_review"):
                st.badge("개인 모의상황실습 작성 완료", color="green")
                for field, title in (
                    ("problem", "문제 정의"), ("hypothesis", "가설"), ("action_plan", "해결안"),
                    ("evidence", "수업 근거"), ("evaluation", "평가와 성찰"),
                ):
                    if answer := record.get(f"ragpbl_{field}"):
                        st.caption(title)
                        st.text(answer)

filtered = []
for item in submissions:
    if not matches_student(item, "student_name"):
        continue
    if selected_status != "전체" and item.get("status") != selected_status:
        continue
    filtered.append(item)

st.subheader(f"제출 자료 {len(filtered)}건", anchor=False)
finals = [item for item in filtered if item.get("activity") == "final_simulation"]
voice_count = sum(
    any(str(file.get("content_type", "")).startswith("audio/") for file in item.get("files", []))
    for item in finals
)
st.caption(f"모의상황실습 최종 제출 {len(finals)}건 · 음성 첨부 {voice_count}건")
st.caption("첨부파일 열기 버튼은 교사가 평가할 때 쓰는 15분짜리 접근 주소를 발급합니다. 주소를 공유하면 만료 전까지 받은 사람이 파일에 접근할 수 있으므로 전달하지 마세요.")
for item in sorted(filtered, key=lambda record: str(record.get("submitted_at", "")), reverse=True):
    submission_id = str(item.get("submission_id", ""))
    if item.get("activity") == "final_simulation":
        label = f"{item.get('team_name') or '모둠'} 모둠 최종 제출 · 제출자 {item.get('student_name', '')}"
    elif item.get("submission_type") == "팀":
        label = f"{item.get('team_name') or '모둠'} 팀 자료 · 제출자 {item.get('student_name', '')}"
    else:
        student_number = "" if code_mode else f"{item.get('student_number', '')} "
        label = f"개인 자료 · {student_number}{item.get('student_name', '')}"
    title = f"{item.get('class_id', '')} · {label} · {item.get('unit_name', '단원 미입력')}"
    with st.expander(title):
        if item.get("activity") == "final_simulation":
            st.badge("모의상황실습 최종 제출", color="green")
            st.text(item.get("simulation_title", ""))
        if item.get("team_members"):
            st.text(f"{item.get('team_name') or '모둠'} · {item['team_members']}")
        st.text(item.get("reflection") or "성찰 내용 없음")
        st.caption(
            f"제출 유형: {item.get('submission_type', '개인')} · "
            f"상태: {status_label(item.get('status', 'submitted'))} · 제출번호 {submission_id[:8]}"
        )
        if evaluator := evaluator_label(item):
            st.caption(f"마지막 평가 교사: {evaluator}")
        for index, file_info in enumerate(item.get("files", [])):
            render_attachment(item, index, file_info)

        st.button(
            "루브릭 기준 열기 · 항목별 채점", key=f"rubric_{submission_id}", type="primary",
            on_click=lambda selected=submission_id: st.session_state.update(hq_active_rubric=selected),
        )
        rubric_id = rubric_for_submission(item)
        details = item.get("rubric_details") or {}
        rubric_scores = details.get("scores") if details.get("id") == rubric_id else None
        if rubric_scores:
            st.caption(" · ".join(f"{label} {rubric_scores.get(key, 0)}/25" for key, label, _ in RUBRICS[rubric_id][1]))

        with st.form(f"feedback_{submission_id}"):
            score = st.slider("평가 총점", 0, 100, int(item.get("rubric_score") or 0), disabled=bool(rubric_scores),
                              help="항목별 채점을 저장한 뒤에는 루브릭 팝업에서 점수를 수정합니다.")
            feedback = st.text_area(
                "교사 피드백",
                value=str(item.get("teacher_feedback", "")),
                max_chars=5000,
                key=f"manual_feedback_{submission_id}",
            )
            status = evaluation_status_selector(item, f"manual_status_{submission_id}")
            save = st.form_submit_button("평가 저장", type="primary", disabled=not rubric_save_available)
        if save:
            try:
                backend.save_teacher_feedback(identity, submission_id, score, feedback, status, rubric_scores=rubric_scores)
                st.success("교사 평가를 저장했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(f"평가 저장 실패: {type(exc).__name__}")

if not filtered:
    st.info("조건에 맞는 제출 자료가 없습니다.")

if active_rubric := st.session_state.get("hq_active_rubric"):
    selected_item = next((item for item in filtered if item.get("submission_id") == active_rubric), None)
    if selected_item:
        show_rubric_dialog(selected_item)
    else:
        close_rubric_dialog()
