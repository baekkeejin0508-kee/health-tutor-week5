"""Run: streamlit run app.py
HEALTH QUEST — 예비 보건의료인의 미션룸 (학생 참여형 4단계 미션 & 활동지 출력 플랫폼)
"""
import importlib
import streamlit as st
import quest_data
import quest_engine
import quest_ui

# 모듈 수정 시 Streamlit 런타임에 즉시 반영되도록 핫 리로드 적용
importlib.reload(quest_data)
importlib.reload(quest_engine)
importlib.reload(quest_ui)

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
    "STEP 01 · 오늘의 미션",
    "STEP 02 · 상황 선택",
    "STEP 03 · 미션 수행",
    "STEP 04 · 활동지 완성",
]

current_nav = st.session_state.get("hq_nav_view", "STEP 01 · 오늘의 미션")
if current_nav not in NAV_OPTIONS:
    current_nav = "STEP 01 · 오늘의 미션"
    st.session_state["hq_nav_view"] = current_nav

# ---------------------------------------------------------
# 사이드바 구성 (간결하고 정돈된 수업 메뉴)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="notranslate" translate="no" style="padding-bottom: 0.4rem;">
            <div style="font-size: 0.72rem; font-weight: 700; color: #0D9488; letter-spacing: 0.08em; margin-bottom: 0.2rem;">CLINICAL PBL PLATFORM</div>
            <h2 style="margin: 0; padding: 0; font-size: 1.15rem; font-weight: 700; line-height: 1.35;">{SITE_CONFIG['site_title']}</h2>
            <div style="font-size: 0.8rem; color: #475569; margin-top: 6px; margin-bottom: 8px; line-height: 1.45;">{SITE_CONFIG['subtitle']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_nav = st.radio(
        "학습 단계 (순서대로 진행)",
        NAV_OPTIONS,
        index=NAV_OPTIONS.index(current_nav),
    )
    if selected_nav != current_nav:
        st.session_state["hq_nav_view"] = selected_nav
        st.rerun()

    st.markdown("<hr style='margin: 1rem 0; border-color: #E2DDD3;'>", unsafe_allow_html=True)
    st.markdown("**학습 단원 선택**")
    unit_names = list(UNIT_CATALOG.keys())
    cur_unit = st.session_state.get("hq_selected_unit", unit_names[0])
    chosen_unit = st.selectbox(
        "오늘의 실습 단원",
        unit_names,
        index=unit_names.index(cur_unit) if cur_unit in unit_names else 0,
        label_visibility="collapsed",
    )
    if chosen_unit != cur_unit:
        st.session_state["hq_selected_unit"] = chosen_unit
        first_scen = UNIT_CATALOG[chosen_unit]["scenarios"][0]["scenario_id"]
        st.session_state["hq_selected_scenario_id"] = first_scen
        st.session_state["hq_active_mission_idx"] = 0
        st.rerun()

    st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)
    reduce_motion_val = st.toggle(
        "화면 전환 효과 줄이기",
        value=st.session_state.get("hq_reduce_motion", False),
        help="축하 효과 등 화면 움직임을 줄이고 차분하게 학습합니다.",
    )
    if reduce_motion_val != st.session_state.get("hq_reduce_motion", False):
        st.session_state["hq_reduce_motion"] = reduce_motion_val
        st.rerun()

    st.markdown("<hr style='margin: 1rem 0; border-color: #E2DDD3;'>", unsafe_allow_html=True)
    if st.button("처음 단계(STEP 01)로 돌아가기", use_container_width=True):
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_nav_view"] = "STEP 01 · 오늘의 미션"
        st.rerun()

# ---------------------------------------------------------
# 상단 공통 헤더 및 1~4단계 균형 탭 버튼
# ---------------------------------------------------------
scen_now = get_current_scenario_data()
done_cnt, total_cnt, prog_ratio = get_scenario_progress(scen_now)

st.markdown(
    f"""
    <div class="notranslate" translate="no" style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:0.5rem; margin-bottom: 0.85rem;">
        <div>
            <div style="margin-bottom: 0.35rem;">
                <span class="hq-badge-teal">실습 단원 · {st.session_state['hq_selected_unit']}</span>
                <span class="hq-badge-navy">미션 진행률 · {done_cnt} / {total_cnt}단계 완료</span>
            </div>
            <h1 style="margin: 0; font-size: 1.78rem; font-weight: 700; letter-spacing: -0.025em;">
                {SITE_CONFIG['site_title']}
            </h1>
        </div>
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

st.markdown("<hr style='margin: 0.65rem 0 1.25rem 0; border-color: #E5E0D5;'>", unsafe_allow_html=True)

# 1회성 배지 획득 / 시나리오 완주 알림 표시
render_one_time_notifications()

# ---------------------------------------------------------
# 선택된 단계 화면 렌더링
# ---------------------------------------------------------
active_view = st.session_state.get("hq_nav_view", "STEP 01 · 오늘의 미션")

if active_view == "STEP 01 · 오늘의 미션":
    render_home_dashboard()

elif active_view == "STEP 02 · 상황 선택":
    render_unit_inquiry_and_scenario_selection()

elif active_view == "STEP 03 · 미션 수행":
    render_mission_runner()

elif active_view == "STEP 04 · 활동지 완성":
    render_collaboration_and_growth()
