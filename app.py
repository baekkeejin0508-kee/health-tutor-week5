"""Run: streamlit run app.py
HEALTH QUEST — 간호 미션룸 (트렌디 에듀테크 스마트 디지털 학습지)
- 공공 무료 폰트 적용: 네이버 나눔스퀘어라운드(OFL 1.1) & 지마켓 산스(무료 공개 라이선스)
"""
import html
import streamlit as st
from quest_ai import get_ai_status
from quest_data import SITE_CONFIG, UNIT_CATALOG
from quest_engine import (
    export_submitted_reports_xlsx,
    init_quest_state,
    load_submitted_reports,
)
from quest_ui import (
    _md_html,
    inject_quest_css,
    render_collaboration_and_growth,
    render_mission_runner,
    render_one_time_notifications,
    render_progress_tracker_board,
    render_sound_effects,
    render_unit_inquiry_and_scenario_selection,
)

st.set_page_config(
    page_title=SITE_CONFIG["site_title"],
    page_icon="🩺",
    layout="wide",
)

# 크롬 자동 번역 왜곡 방지
_md_html(
    """
    <meta name="google" content="notranslate">
    <style>
        .notranslate, [translate="no"] {
            translate: no !important;
        }
    </style>
    """
)

init_quest_state()
inject_quest_css(reduce_motion=st.session_state.get("hq_reduce_motion", False))

NAV_OPTIONS = [
    "STEP 01 · 단원 질문 & 피드백",
    "STEP 02 · 기초·중급·심화 실습",
    "STEP 03 · 팀 협력 & 교사 피드백",
]

NAV_SHORT_LABELS = {
    NAV_OPTIONS[0]: "1. 단원 질문과 피드백",
    NAV_OPTIONS[1]: "2. 단계별 PBL 실습",
    NAV_OPTIONS[2]: "3. 팀 협력과 교사 피드백",
}

TOP_NAV_LABELS = ["단원 질문", "단계별 실습", "협력·피드백"]

current_nav = st.session_state.get("hq_nav_view", NAV_OPTIONS[0])
if current_nav not in NAV_OPTIONS:
    current_nav = NAV_OPTIONS[0]
    st.session_state["hq_nav_view"] = current_nav


def _on_sidebar_nav_change():
    st.session_state["hq_nav_view"] = st.session_state["hq_sidebar_nav_radio"]
    st.session_state["hq_pending_sound"] = "pop"


def _unit_display_name(unit_name: str) -> str:
    """선택 상자에서는 앞의 [교과목명]을 숨기되 내부 단원 키는 유지합니다."""
    if unit_name.startswith("[") and "] " in unit_name:
        return unit_name.split("] ", 1)[1]
    return unit_name


# ---------------------------------------------------------
# 사이드바 (간결하고 산뜻한 구성을 적용)
# ---------------------------------------------------------
with st.sidebar:
    _md_html(
        f"""
        <div class="hq-sidebar-brand notranslate" translate="no">
            <div class="hq-sidebar-eyebrow">HEALTH QUEST</div>
            <div class="hq-sidebar-title">{html.escape(SITE_CONFIG['site_title'])}</div>
            <div class="hq-sidebar-copy">보건간호 PBL 디지털 워크북</div>
        </div>
        """
    )
    st.markdown("**1. 과목 및 단원 선택**")
    subjects = ["전체 교과목 보기", "기초간호임상실무", "간호의 기초", "보건간호", "공중보건", "인체구조와 기능"]
    chosen_subj = st.selectbox("교과목", subjects, index=0)

    all_unit_names = list(UNIT_CATALOG.keys())
    if chosen_subj == "전체 교과목 보기":
        filtered_units = all_unit_names
    else:
        filtered_units = [u for u in all_unit_names if UNIT_CATALOG[u].get("subject") == chosen_subj] or all_unit_names

    cur_unit = st.session_state.get("hq_selected_unit", filtered_units[0])
    if cur_unit not in filtered_units:
        cur_unit = filtered_units[0]
        st.session_state["hq_selected_unit"] = cur_unit
        st.session_state["hq_selected_scenario_id"] = UNIT_CATALOG[cur_unit]["scenarios"][0]["scenario_id"]
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_selected_term_idx"] = 0

    chosen_unit = st.selectbox(
        "실습 단원",
        filtered_units,
        index=filtered_units.index(cur_unit),
        format_func=_unit_display_name,
    )
    if chosen_unit != st.session_state.get("hq_selected_unit"):
        st.session_state["hq_selected_unit"] = chosen_unit
        st.session_state["hq_selected_scenario_id"] = UNIT_CATALOG[chosen_unit]["scenarios"][0]["scenario_id"]
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_selected_term_idx"] = 0
        st.session_state["hq_pending_sound"] = "chime"
        st.rerun()

    _md_html("<hr style='margin: 0.6rem 0; border-color: #E0E7FF;'>")
    st.session_state["hq_sidebar_nav_radio"] = st.session_state["hq_nav_view"]
    st.radio(
        "2. 학습 단계",
        NAV_OPTIONS,
        format_func=lambda value: NAV_SHORT_LABELS[value],
        key="hq_sidebar_nav_radio",
        on_change=_on_sidebar_nav_change,
    )

    _md_html("<hr style='margin: 0.6rem 0; border-color: #E0E7FF;'>")
    sound_val = st.toggle(
        "효과음 켜기",
        value=st.session_state.get("hq_sound_enabled", False),
    )
    if sound_val != st.session_state.get("hq_sound_enabled", False):
        st.session_state["hq_sound_enabled"] = sound_val
        st.rerun()

    reduce_motion_val = st.toggle(
        "화면 효과 줄이기",
        value=st.session_state.get("hq_reduce_motion", False),
    )
    if reduce_motion_val != st.session_state.get("hq_reduce_motion", False):
        st.session_state["hq_reduce_motion"] = reduce_motion_val
        st.rerun()

    with st.container(key="sidebar_home_palette"):
        if st.button("처음 단계로 이동", key="sidebar_home", use_container_width=True):
            st.session_state["hq_active_mission_idx"] = 0
            st.session_state["hq_nav_view"] = NAV_OPTIONS[0]
            st.session_state["hq_pending_sound"] = "pop"
            st.rerun()

    st.info("학습이 끝나면 마지막 단계에서 ‘내 제출용 Excel 받기’를 눌러 파일을 저장하고, 선생님이 안내한 제출처에 올리세요.")
    st.caption("브라우저 창을 닫거나 서버가 다시 시작되면 작성 중인 기록이 사라질 수 있으니, 완료 후 Excel 파일을 꼭 저장하세요.")

    ai_status = get_ai_status()
    if ai_status["configured"]:
        st.caption("AI 피드백: 수업 자료 RAG · 보건튜터 팀 연결됨")
    else:
        st.caption("AI 피드백: 규칙형 안전 모드 · 서버 AI 설정 확인 필요")

    with st.expander("선생님용 제출 관리"):
        reps = load_submitted_reports()
        st.caption(f"현재 이 앱에 제출된 기록: {len(reps)}건")
        st.download_button(
            label=f"전체 제출물 Excel 받기 ({len(reps)}건)",
            data=export_submitted_reports_xlsx(),
            file_name="HEALTH_QUEST_학생제출보고서_전체목록.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="sidebar_teacher_excel_dl",
        )
        st.caption("현재는 선생님 인증이 없는 시연 기능입니다. 실제 수업 배포 전에는 교사 로그인과 Firebase 저장소 연결이 필요합니다.")

# ---------------------------------------------------------
# 상단 히어로 배너 (세련되고 간결한 구성)
# ---------------------------------------------------------
cur_unit_obj = UNIT_CATALOG[st.session_state["hq_selected_unit"]]
custom_topic_str = st.session_state.get("hq_custom_unit_topic", "")
topic_badge_html = f"<span class='hq-hero-pill'>{html.escape(custom_topic_str)}</span>" if custom_topic_str else ""

_md_html(
    f"""
    <div class="hq-hero-banner notranslate" translate="no">
        <div>
            <span class="hq-hero-pill">{html.escape(cur_unit_obj.get('subject', '보건간호'))}</span>
            <span class="hq-hero-pill">{html.escape(st.session_state['hq_selected_unit'])}</span>
            {topic_badge_html}
        </div>
        <h1>{html.escape(SITE_CONFIG['site_title'])}</h1>
        <div class="hq-hero-sub">개념을 묻고, 임상 상황을 판단하고, 팀으로 해결하는 PBL 실습</div>
    </div>
    """
)

# 실시간 진도율 보드
render_progress_tracker_board()

# 상단 3단계 네비게이션 탭 버튼
with st.container(key="top_nav_palette"):
    top_cols = st.columns(3, gap="small")
    for idx, label in enumerate(NAV_OPTIONS):
        btn_kind = "primary" if st.session_state["hq_nav_view"] == label else "secondary"
        with top_cols[idx]:
            if st.button(TOP_NAV_LABELS[idx], key=f"top_nav_{idx}", type=btn_kind, use_container_width=True):
                st.session_state["hq_nav_view"] = label
                st.session_state["hq_pending_sound"] = "chime"
                st.rerun()

_md_html("<hr style='margin: 0.55rem 0 0.95rem 0; border-color: #E0E7FF;'>")

render_one_time_notifications()

# ---------------------------------------------------------
# 선택된 단계 화면 렌더링
# ---------------------------------------------------------
active_view = st.session_state.get("hq_nav_view", NAV_OPTIONS[0])

if active_view == "STEP 01 · 단원 질문 & 피드백":
    render_unit_inquiry_and_scenario_selection()

elif active_view == "STEP 02 · 기초·중급·심화 실습":
    render_mission_runner()

elif active_view == "STEP 03 · 팀 협력 & 교사 피드백":
    render_collaboration_and_growth()

render_sound_effects()
