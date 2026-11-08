"""Run: streamlit run app.py
HEALTH QUEST — 예비 보건의료인의 미션룸 (스마트 디지털 보건간호 PBL 학습지 플랫폼)
- 수업 흐름: 단원 질문(2~3개) & AI 피드백 → 수준별 모의실습 3개(기초·중급·심화) 개인 PBL 서술 & AI 개인 피드백 → 팀별 협력 서술 & AI 팀 피드백 → 교사 최종 피드백 및 학습지 출력
"""
import importlib
import streamlit as st
import quest_data
import quest_engine
import quest_ui

# 코드 수정 시 Streamlit 런타임에 즉시 반영되도록 핫 리로드 적용
importlib.reload(quest_data)
importlib.reload(quest_engine)
importlib.reload(quest_ui)

from quest_data import SITE_CONFIG, UNIT_CATALOG
from quest_engine import init_quest_state
from quest_ui import (
    inject_quest_css,
    render_collaboration_and_growth,
    render_mission_runner,
    render_one_time_notifications,
    render_progress_tracker_board,
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
    "STEP 01 · 단원 질문 & 피드백",
    "STEP 02 · 기초·중급·심화 실습",
    "STEP 03 · 팀 협력 & 교사 피드백",
]

current_nav = st.session_state.get("hq_nav_view", NAV_OPTIONS[0])
if current_nav not in NAV_OPTIONS:
    current_nav = NAV_OPTIONS[0]
    st.session_state["hq_nav_view"] = current_nav

# ---------------------------------------------------------
# 사이드바 구성 (전 교과서 과목·단원 선택 및 수업 단계 이동)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"""
        <div class="notranslate" translate="no" style="padding-bottom: 0.35rem;">
            <div style="font-size: 0.72rem; font-weight: 700; color: #0D9488; letter-spacing: 0.06em; margin-bottom: 0.15rem;">SMART DIGITAL PBL WORKSHEET</div>
            <h2 style="margin: 0; padding: 0; font-size: 1.12rem; font-weight: 700; line-height: 1.35;">{SITE_CONFIG['site_title']}</h2>
            <div style="font-size: 0.79rem; color: #475569; margin-top: 5px; line-height: 1.42;">{SITE_CONFIG['subtitle']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='margin: 0.75rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    st.markdown("**1. 교과서 과목 및 단원 선택**")

    subjects = ["전체 교과목 보기", "기초간호임상실무", "간호의 기초", "보건간호", "공중보건", "인체구조와 기능"]
    chosen_subj = st.selectbox("교과목 필터", subjects, index=0)

    all_unit_names = list(UNIT_CATALOG.keys())
    if chosen_subj == "전체 교과목 보기":
        filtered_units = all_unit_names
    else:
        filtered_units = [u for u in all_unit_names if UNIT_CATALOG[u].get("subject") == chosen_subj]
        if not filtered_units:
            filtered_units = all_unit_names

    cur_unit = st.session_state.get("hq_selected_unit", filtered_units[0])
    if cur_unit not in filtered_units:
        cur_unit = filtered_units[0]

    chosen_unit = st.selectbox(
        "학습할 단원 선택",
        filtered_units,
        index=filtered_units.index(cur_unit),
    )
    if chosen_unit != st.session_state.get("hq_selected_unit"):
        st.session_state["hq_selected_unit"] = chosen_unit
        first_scen = UNIT_CATALOG[chosen_unit]["scenarios"][0]["scenario_id"]
        st.session_state["hq_selected_scenario_id"] = first_scen
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_selected_term_idx"] = 0
        st.rerun()

    st.markdown("<hr style='margin: 0.75rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    selected_nav = st.radio(
        "2. 수업 진행 단계",
        NAV_OPTIONS,
        index=NAV_OPTIONS.index(current_nav),
    )
    if selected_nav != current_nav:
        st.session_state["hq_nav_view"] = selected_nav
        st.rerun()

    st.markdown("<hr style='margin: 0.75rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    reduce_motion_val = st.toggle(
        "화면 전환 효과 줄이기",
        value=st.session_state.get("hq_reduce_motion", False),
        help="축하 풍선 등 화면 효과를 끄고 학습에 집중합니다.",
    )
    if reduce_motion_val != st.session_state.get("hq_reduce_motion", False):
        st.session_state["hq_reduce_motion"] = reduce_motion_val
        st.rerun()

    if st.button("처음 단계(STEP 01)로 이동", use_container_width=True):
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_nav_view"] = NAV_OPTIONS[0]
        st.rerun()

# ---------------------------------------------------------
# 상단 공통 헤더 및 실시간 학습 진도 보드 + 3단계 탭 버튼
# ---------------------------------------------------------
cur_unit_obj = UNIT_CATALOG[st.session_state["hq_selected_unit"]]
custom_topic_str = st.session_state.get("hq_custom_unit_topic", "")
topic_badge_html = f"<span class='hq-badge-inter'>세부 주제 · {custom_topic_str}</span>" if custom_topic_str else ""

st.markdown(
    f"""
    <div class="notranslate" translate="no" style="margin-bottom: 0.55rem;">
        <div style="margin-bottom: 0.3rem;">
            <span class="hq-badge-teal">교과목 · {cur_unit_obj.get('subject', '보건간호')}</span>
            <span class="hq-badge-navy">현재 단원 · {st.session_state['hq_selected_unit']}</span>
            {topic_badge_html}
        </div>
        <h1 style="margin: 0; font-size: 1.72rem; font-weight: 800; letter-spacing: -0.025em;">
            {SITE_CONFIG['site_title']}
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# 실시간 진도율(%) 및 5단계 체크 트래커 보드 렌더링
render_progress_tracker_board()

# 상단 3단계 네비게이션 탭 버튼
top_cols = st.columns(3, gap="small")
for idx, label in enumerate(NAV_OPTIONS):
    btn_kind = "primary" if st.session_state["hq_nav_view"] == label else "secondary"
    with top_cols[idx]:
        if st.button(label, key=f"top_nav_{idx}", type=btn_kind, use_container_width=True):
            st.session_state["hq_nav_view"] = label
            st.rerun()

st.markdown("<hr style='margin: 0.6rem 0 1.1rem 0; border-color: #CBD5E1;'>", unsafe_allow_html=True)

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
