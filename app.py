"""Run: streamlit run app.py
HEALTH QUEST — 예비 보건의료인의 미션룸 (특성화고등학교 간호학과 참여형 학습 플랫폼)
"""
import streamlit as st
from quest_data import SITE_CONFIG, UNIT_CATALOG
from quest_engine import get_current_scenario_data, get_scenario_progress, init_quest_state
from quest_ui import (
    inject_quest_css,
    render_collaboration_and_growth,
    render_home_dashboard,
    render_mission_runner,
    render_one_time_notifications,
    render_unit_inquiry_and_scenario_selection,
)

st.set_page_config(
    page_title=SITE_CONFIG["site_title"],
    page_icon="🩺",
    layout="wide",
)

# 크롬 웹페이지 자동 번역으로 인한 한글 왜곡 방지
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
        .notranslate, [translate="no"] {
            translate: no !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

init_quest_state()
inject_quest_css(reduce_motion=st.session_state.get("hq_reduce_motion", False))

NAV_OPTIONS = [
    "🏠 미션룸 홈",
    "🧭 단원 질문 & 실습상황 선택",
    "🩺 단계별 미션 수행",
    "🤝 팀 협력학습 & 성장 기록",
]

current_nav = st.session_state.get("hq_nav_view", "🏠 미션룸 홈")
if current_nav not in NAV_OPTIONS:
    current_nav = "🏠 미션룸 홈"
    st.session_state["hq_nav_view"] = current_nav

# ---------------------------------------------------------
# 사이드바 구성 (오직 학생 수업 몰입에 필요한 핵심 메뉴만 배치)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="notranslate" translate="no">
            <h2 style="margin: 0; padding: 0; font-size: 1.15rem; font-weight: 700;">🩺 {SITE_CONFIG['site_title']}</h2>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 4px; margin-bottom: 10px;">{SITE_CONFIG['subtitle']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_nav = st.radio(
        "학습 단계 이동",
        NAV_OPTIONS,
        index=NAV_OPTIONS.index(current_nav),
    )
    if selected_nav != current_nav:
        st.session_state["hq_nav_view"] = selected_nav
        st.rerun()

    st.markdown("---")
    st.subheader("📘 학습 단원 및 화면 설정")
    unit_names = list(UNIT_CATALOG.keys())
    cur_unit = st.session_state.get("hq_selected_unit", unit_names[0])
    chosen_unit = st.selectbox(
        "실습 단원 선택",
        unit_names,
        index=unit_names.index(cur_unit) if cur_unit in unit_names else 0,
    )
    if chosen_unit != cur_unit:
        st.session_state["hq_selected_unit"] = chosen_unit
        first_scen = UNIT_CATALOG[chosen_unit]["scenarios"][0]["scenario_id"]
        st.session_state["hq_selected_scenario_id"] = first_scen
        st.session_state["hq_active_mission_idx"] = 0
        st.rerun()

    reduce_motion_val = st.toggle(
        "✨ 애니메이션 줄이기 (동작 감소)",
        value=st.session_state.get("hq_reduce_motion", False),
        help="화면 전환 및 축하 효과를 줄이고 글과 아이콘 중심으로 학습합니다.",
    )
    if reduce_motion_val != st.session_state.get("hq_reduce_motion", False):
        st.session_state["hq_reduce_motion"] = reduce_motion_val
        st.rerun()

    st.markdown("---")
    if st.button("🔄 현재 단원 처음부터 다시 도전", use_container_width=True):
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_nav_view"] = "🏠 미션룸 홈"
        st.rerun()

# ---------------------------------------------------------
# 상단 공통 헤더 및 4단계 핵심 학습 흐름 바로가기 버튼
# ---------------------------------------------------------
scen_now = get_current_scenario_data()
done_cnt, total_cnt, prog_ratio = get_scenario_progress(scen_now)

st.markdown(
    f"""
    <div class="notranslate" translate="no" style="margin-bottom: 0.6rem;">
        <span class="hq-badge-teal">{SITE_CONFIG['target_audience']}</span>
        <span class="hq-badge-navy">현재 단원: {st.session_state['hq_selected_unit']}</span>
        <span class="hq-badge-coral">미션 진행률: {done_cnt}/{total_cnt} ({int(prog_ratio * 100)}%)</span>
        <h1 style="margin: 0.25rem 0 0.1rem 0; font-size: 1.9rem; font-weight: 800;">
            {SITE_CONFIG['site_title']}
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

top_cols = st.columns(4, gap="small")
for idx, label in enumerate(NAV_OPTIONS):
    btn_kind = "primary" if st.session_state["hq_nav_view"] == label else "secondary"
    with top_cols[idx]:
        if st.button(label, key=f"top_nav_{idx}", type=btn_kind, use_container_width=True):
            st.session_state["hq_nav_view"] = label
            st.rerun()

st.markdown("<hr style='margin: 0.6rem 0 1.1rem 0; border-color: #E5E0D5;'>", unsafe_allow_html=True)

# 1회성 배지 획득 / 시나리오 완주 알림 표시
render_one_time_notifications()

# ---------------------------------------------------------
# 선택된 화면 렌더링
# ---------------------------------------------------------
active_view = st.session_state.get("hq_nav_view", "🏠 미션룸 홈")

if active_view == "🏠 미션룸 홈":
    render_home_dashboard()

elif active_view == "🧭 단원 질문 & 실습상황 선택":
    render_unit_inquiry_and_scenario_selection()

elif active_view == "🩺 단계별 미션 수행":
    render_mission_runner()

elif active_view == "🤝 팀 협력학습 & 성장 기록":
    render_collaboration_and_growth()
