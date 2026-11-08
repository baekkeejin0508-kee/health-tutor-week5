"""Run: streamlit run app.py
HEALTH QUEST — 예비 보건의료인의 미션룸 (스마트 디지털 보건간호 PBL 학습지 플랫폼)
- 수업 흐름: 단원 질문(2~3개) & AI 피드백 → 수준별 모의실습 3개(기초·중급·심화) 개인 PBL 서술 & AI 개인 피드백 → 팀별 협력 서술 & AI 팀 피드백 → 교사 최종 피드백 및 보고서 제출함·인쇄
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

# 크롬 웹페이지 자동 번역으로 인한 한글 왜곡 방지
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
# 사이드바 구성 (전 교과서 과목·단원 선택, 효과음 설정, 교사용 제출물 다운로드)
# ---------------------------------------------------------
with st.sidebar:
    _md_html(
        f"""
        <div class="notranslate" translate="no" style="background:linear-gradient(135deg, #4F46E5 0%, #0EA5E9 100%); padding: 0.9rem 1rem; border-radius: 14px; color: #FFFFFF; margin-bottom: 0.5rem; box-shadow: 0 4px 12px rgba(79,70,229,0.2);">
            <div style="font-size: 0.72rem; font-weight: 800; color: #E0F2FE; letter-spacing: 0.06em; margin-bottom: 0.2rem;">✨ SMART DIGITAL WORKSHEET</div>
            <div style="margin: 0; font-size: 1.05rem; font-weight: 800; color: #FFFFFF; line-height: 1.35;">{html.escape(SITE_CONFIG['site_title'])}</div>
            <div style="font-size: 0.77rem; color: #E0E7FF; margin-top: 4px; line-height: 1.4;">{html.escape(SITE_CONFIG['subtitle'])}</div>
        </div>
        """
    )

    _md_html("<hr style='margin: 0.65rem 0; border-color: #C7D2FE;'>")
    st.markdown("**📚 1. 교과서 과목 및 단원 선택**")

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
        st.session_state["hq_selected_unit"] = cur_unit
        st.session_state["hq_selected_scenario_id"] = UNIT_CATALOG[cur_unit]["scenarios"][0]["scenario_id"]
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_selected_term_idx"] = 0

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
        st.session_state["hq_pending_sound"] = "chime"
        st.rerun()

    _md_html("<hr style='margin: 0.65rem 0; border-color: #C7D2FE;'>")
    st.session_state["hq_sidebar_nav_radio"] = st.session_state["hq_nav_view"]
    st.radio(
        "🧭 2. 수업 진행 단계",
        NAV_OPTIONS,
        key="hq_sidebar_nav_radio",
        on_change=_on_sidebar_nav_change,
    )

    _md_html("<hr style='margin: 0.65rem 0; border-color: #C7D2FE;'>")
    sound_val = st.toggle(
        "🔊 버튼 클릭음 · 효과음 켜기",
        value=st.session_state.get("hq_sound_enabled", True),
        help="버튼을 누를 때 통통 튀는 효과음과 미션 성공 팡파르 소리를 재생합니다.",
    )
    if sound_val != st.session_state.get("hq_sound_enabled", True):
        st.session_state["hq_sound_enabled"] = sound_val
        st.rerun()

    reduce_motion_val = st.toggle(
        "✨ 화면 움직임 줄이기",
        value=st.session_state.get("hq_reduce_motion", False),
        help="축하 풍선 등 화면 효과를 줄이고 학습에 집중합니다.",
    )
    if reduce_motion_val != st.session_state.get("hq_reduce_motion", False):
        st.session_state["hq_reduce_motion"] = reduce_motion_val
        st.rerun()

    if st.button("🏠 처음 단계(STEP 01)로 이동", use_container_width=True):
        st.session_state["hq_active_mission_idx"] = 0
        st.session_state["hq_nav_view"] = NAV_OPTIONS[0]
        st.session_state["hq_pending_sound"] = "pop"
        st.rerun()

    _md_html("<hr style='margin: 0.65rem 0; border-color: #C7D2FE;'>")
    with st.expander("👩‍🏫 교사용 제출 보고서 관리함"):
        reps = load_submitted_reports()
        st.caption(f"현재 제출 완료: **{len(reps)}명**")
        st.download_button(
            label=f"📊 전체 엑셀(CSV) 다운로드 ({len(reps)}건)",
            data=export_submitted_reports_csv(),
            file_name="HEALTH_QUEST_학생제출보고서_전체목록.csv",
            mime="text/csv",
            use_container_width=True,
            key="sidebar_csv_dl",
        )

# ---------------------------------------------------------
# 상단 히어로 배너 (코드 태그 노출 원천 차단 + 사설 디지털 학습지 감성 컬러)
# ---------------------------------------------------------
cur_unit_obj = UNIT_CATALOG[st.session_state["hq_selected_unit"]]
custom_topic_str = st.session_state.get("hq_custom_unit_topic", "")
topic_badge_html = (
    f"<span class='hq-hero-pill'>✨ 세부 주제 · {html.escape(custom_topic_str)}</span>"
    if custom_topic_str
    else ""
)

_md_html(
    f"""
    <div class="hq-hero-banner notranslate" translate="no">
        <div>
            <span class="hq-hero-pill">📘 교과목 · {html.escape(cur_unit_obj.get('subject', '보건간호'))}</span>
            <span class="hq-hero-pill">🩺 현재 단원 · {html.escape(st.session_state['hq_selected_unit'])}</span>
            {topic_badge_html}
        </div>
        <h1>{html.escape(SITE_CONFIG['site_title'])}</h1>
        <div class="hq-hero-sub">자기주도 질문(2~3개) → 기초·중급·심화 PBL 모의실습 → 팀 협력 & AI·교사 피드백 스마트 디지털 학습지</div>
    </div>
    """
)

# 실시간 진도율(%) 및 5단계 체크 트래커 보드 렌더링
render_progress_tracker_board()

# 상단 3단계 네비게이션 탭 버튼 (3D 입체 버튼)
top_cols = st.columns(3, gap="small")
for idx, label in enumerate(NAV_OPTIONS):
    btn_kind = "primary" if st.session_state["hq_nav_view"] == label else "secondary"
    with top_cols[idx]:
        if st.button(label, key=f"top_nav_{idx}", type=btn_kind, use_container_width=True):
            st.session_state["hq_nav_view"] = label
            st.session_state["hq_pending_sound"] = "chime"
            st.rerun()

_md_html("<hr style='margin: 0.65rem 0 1.1rem 0; border-color: #C7D2FE;'>")

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

# Web Audio API 클릭 효과음 및 완료 차임벨/팡파르 사운드 엔진 실행
render_sound_effects()
