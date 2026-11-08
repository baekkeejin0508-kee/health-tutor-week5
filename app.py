"""Run: streamlit run app.py
HEALTH QUEST — 예비 보건의료인의 미션룸 (트렌디 에듀테크 스마트 디지털 학습지)
- 공공 무료 폰트 적용: 네이버 나눔스퀘어라운드(OFL 1.1) & 지마켓 산스(무료 공개 라이선스)
"""
import html
import streamlit as st
from quest_data import SITE_CONFIG, UNIT_CATALOG
from quest_engine import (
    export_submitted_reports_csv,
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

current_nav = st.session_state.get("hq_nav_view", NAV_OPTIONS[0])
if current_nav not in NAV_OPTIONS:
    current_nav = NAV_OPTIONS[0]
    st.session_state["hq_nav_view"] = current_nav


def _on_sidebar_nav_change():
    st.session_state["hq_nav_view"] = st.session_state["hq_sidebar_nav_radio"]
    st.session_state["hq_pending_sound"] = "pop"


# ---------------------------------------------------------
# 사이드바 (간결하고 산뜻한 구성을 적용)
# ---------------------------------------------------------
with st.sidebar:
    _md_html(
        f"""
        <div class="hq-sidebar-brand notranslate" translate="no">
            <div style="font-size: 0.72rem; font-weight: 800; opacity: 0.9; letter-spacing: 0.05em;">✨ SMART PBL WORKSHEET</div>
            <div style="font-size: 1.03rem; font-weight: 800; margin-top: 3px; line-height: 1.35;">🩺 {html.escape(SITE_CONFIG['site_title'])}</div>
        </div>
        """
    )

    st.markdown("**📚 1. 과목 및 단원 선택**")
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

    chosen_unit = st.selectbox("실습 단원", filtered_units, index=filtered_units.index(cur_unit))
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
        "🧭 2. 학습 단계",
        NAV_OPTIONS,
        key="hq_sidebar_nav_radio",
        on_change=_on_sidebar_nav_change,
    )

    _md_html("<hr style='margin: 0.6rem 0; border-color: #E0E7FF;'>")
    sound_val = st.toggle(
        "🔊 효과음 켜기",
        value=st.session_state.get("hq_sound_enabled", True),
    )
    if sound_val != st.session_state.get("hq_sound_enabled", True):
        st.session_state["hq_sound_enabled"] = sound_val
        st.rerun()

    reduce_motion_val = st.toggle(
        "✨ 화면 효과 줄이기",
        value=st.session_state.get("hq_reduce_motion", False),
    )
    if reduce_motion_val != st.session_state.get("hq_reduce_motion", False):
        st.session_state["hq_reduce_motion"] = reduce_motion_val
        st.rerun()

    if st.button("🏠 처음 단계로 이동", use_container_width=True):
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_nav_view"] = NAV_OPTIONS[0]
        st.session_state["hq_pending_sound"] = "pop"
        st.rerun()

    with st.expander("👩‍🏫 교사용 제출함"):
        reps = load_submitted_reports()
        st.caption(f"제출 인원: **{len(reps)}명**")
        st.download_button(
            label=f"📊 엑셀(CSV) 다운로드 ({len(reps)}명)",
            data=export_submitted_reports_csv(),
            file_name="HEALTH_QUEST_학생제출보고서_전체목록.csv",
            mime="text/csv",
            use_container_width=True,
            key="sidebar_csv_dl",
        )

# ---------------------------------------------------------
# 상단 히어로 배너 (세련되고 간결한 구성)
# ---------------------------------------------------------
cur_unit_obj = UNIT_CATALOG[st.session_state["hq_selected_unit"]]
custom_topic_str = st.session_state.get("hq_custom_unit_topic", "")
topic_badge_html = f"<span class='hq-hero-pill'>✨ {html.escape(custom_topic_str)}</span>" if custom_topic_str else ""

_md_html(
    f"""
    <div class="hq-hero-banner notranslate" translate="no">
        <div>
            <span class="hq-hero-pill">📘 {html.escape(cur_unit_obj.get('subject', '보건간호'))}</span>
            <span class="hq-hero-pill">🩺 {html.escape(st.session_state['hq_selected_unit'])}</span>
            {topic_badge_html}
        </div>
        <h1>{html.escape(SITE_CONFIG['site_title'])}</h1>
        <div class="hq-hero-sub">💬 개념 질문 → 🌱💧🔥 기초·중급·심화 PBL 모의실습 → 🏆 팀 협력 & AI·교사 피드백</div>
    </div>
    """
)

# 실시간 진도율 보드
render_progress_tracker_board()

# 상단 3단계 네비게이션 탭 버튼
top_cols = st.columns(3, gap="small")
tab_Icons = ["💬 ", "🩺 ", "🏆 "]
for idx, label in enumerate(NAV_OPTIONS):
    btn_kind = "primary" if st.session_state["hq_nav_view"] == label else "secondary"
    with top_cols[idx]:
        if st.button(f"{tab_Icons[idx]}{label}", key=f"top_nav_{idx}", type=btn_kind, use_container_width=True):
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
