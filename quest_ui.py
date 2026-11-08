"""HEALTH QUEST — 예비 보건의료인의 미션룸: 에디토리얼 스타일 단계별(Step-by-Step) UI·UX 및 활동지 출력 모듈."""
import html
import streamlit as st
import streamlit.components.v1 as components
from quest_data import SITE_CONFIG
from quest_engine import (
    BADGE_DEFINITIONS,
    award_action_once,
    evaluate_mission_submission,
    generate_unit_inquiry_feedback,
    get_current_scenario_data,
    get_current_unit_data,
    get_scenario_progress,
    save_mission_reflection,
)


def inject_quest_css(reduce_motion: bool = False):
    """전문 보건교육 에디토리얼 디자인: 아이보리 배경(#FAF8F5), 딥 네이비 본문(#1B2A4A), 청록 주요 버튼(#0D9488), 코랄 강조(#E05A47)."""
    motion_css = (
        """
        *, *::before, *::after {
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.001ms !important;
            scroll-behavior: auto !important;
        }
        """
        if reduce_motion
        else """
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.001ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.001ms !important;
                scroll-behavior: auto !important;
            }
        }
        """
    )

    st.markdown(
        f"""
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

        :root {{
            color-scheme: light !important;
        }}
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: #FAF8F5 !important;
            color: #1B2A4A !important;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif !important;
            letter-spacing: -0.015em !important;
            word-spacing: 0.02em !important;
            overflow-x: hidden !important;
        }}
        /* 중앙 정렬 및 좌우 대칭 여백 확보 */
        .block-container {{
            max-width: 1080px !important;
            margin: 0 auto !important;
            padding-top: 2rem !important;
            padding-bottom: 3.5rem !important;
            padding-left: 2.2rem !important;
            padding-right: 2.2rem !important;
        }}
        header[data-testid="stHeader"] {{
            background-color: #FAF8F5 !important;
            color: #1B2A4A !important;
            border-bottom: 1px solid #EAE5DC;
        }}
        .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown {{
            color: #1B2A4A !important;
            line-height: 1.72 !important;
            word-break: keep-all !important;
            overflow-wrap: break-word !important;
        }}
        h1, h2, h3, h4 {{
            color: #14223D !important;
            font-family: 'Pretendard', sans-serif !important;
            letter-spacing: -0.025em !important;
            line-height: 1.38 !important;
            word-break: keep-all !important;
        }}
        /* 모든 입력창 흰색 배경 + 딥 네이비 글씨 고정 */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"],
        div[data-baseweb="base-input"],
        textarea,
        input[type="text"] {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
            -webkit-text-fill-color: #1B2A4A !important;
            caret-color: #0D9488 !important;
            font-size: 0.96rem !important;
            letter-spacing: -0.01em !important;
        }}
        textarea:focus,
        input[type="text"]:focus {{
            border-color: #0D9488 !important;
            box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.14) !important;
        }}
        textarea::placeholder,
        input::placeholder {{
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
            opacity: 1 !important;
        }}
        ul[data-baseweb="menu"],
        div[data-baseweb="popover"] div,
        li[role="option"] {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
        }}
        li[role="option"]:hover {{
            background-color: #F0FDFA !important;
        }}
        [data-testid="stForm"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #E5E0D5 !important;
            border-radius: 14px !important;
            padding: 1.5rem 1.6rem !important;
            box-shadow: 0 2px 10px rgba(20, 34, 61, 0.03);
        }}
        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
            border-color: #E5E0D5 !important;
            border-radius: 12px !important;
        }}
        div[role="radiogroup"] label {{
            padding: 0.32rem 0 !important;
        }}
        div[role="radiogroup"] label > div:first-child {{
            background-color: #FFFFFF !important;
            border: 2px solid #0D9488 !important;
        }}
        section[data-testid="stSidebar"] {{
            background-color: #F3F0EA !important;
            border-right: 1px solid #E5E0D5;
        }}
        section[data-testid="stSidebar"] * {{
            color: #1B2A4A !important;
        }}
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] input {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
            -webkit-text-fill-color: #1B2A4A !important;
        }}
        /* 주요 행동 버튼: 청록색(#0D9488) */
        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"],
        div.stDownloadButton > button {{
            background-color: #0D9488 !important;
            color: #FFFFFF !important;
            border: 1px solid #0F766E !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            letter-spacing: -0.01em !important;
            padding: 0.62rem 1.15rem !important;
            transition: transform 0.15s ease, background-color 0.15s ease;
        }}
        div.stButton > button[kind="primary"] *,
        div.stFormSubmitButton > button[kind="primary"] *,
        div.stDownloadButton > button * {{
            color: #FFFFFF !important;
        }}
        div.stButton > button[kind="primary"]:hover,
        div.stFormSubmitButton > button[kind="primary"]:hover,
        div.stDownloadButton > button:hover {{
            background-color: #0F766E !important;
            transform: translateY(-1px);
        }}
        div.stButton > button[kind="secondary"] {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
            font-size: 0.94rem !important;
            letter-spacing: -0.01em !important;
            padding: 0.6rem 1rem !important;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            background-color: #F0FDFA !important;
            border-color: #0D9488 !important;
            color: #0F766E !important;
        }}
        /* 세련된 에디토리얼 카드 레이아웃 */
        .hq-card {{
            background: #FFFFFF;
            border: 1px solid #E5E0D5;
            border-radius: 14px;
            padding: 1.5rem 1.65rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 12px rgba(20, 34, 61, 0.035);
        }}
        .hq-card-selected {{
            background: #FFFFFF;
            border: 1.5px solid #0D9488;
            border-top: 4px solid #0D9488;
            border-radius: 14px;
            padding: 1.5rem 1.65rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 16px rgba(13, 148, 136, 0.07);
        }}
        .hq-card-coral {{
            background: #FFFDFB;
            border: 1px solid #F3DCD8;
            border-left: 4px solid #E05A47;
            border-radius: 14px;
            padding: 1.3rem 1.5rem;
            margin-bottom: 1rem;
        }}
        .hq-scenario-card {{
            min-height: 220px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .hq-badge-teal {{
            display: inline-block;
            background: #E6F7F5;
            color: #0F766E !important;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.01em;
            padding: 0.2rem 0.68rem;
            border-radius: 6px;
            margin-right: 0.4rem;
        }}
        .hq-badge-coral {{
            display: inline-block;
            background: #FCECE9;
            color: #C0392B !important;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.01em;
            padding: 0.2rem 0.68rem;
            border-radius: 6px;
            margin-right: 0.4rem;
        }}
        .hq-badge-navy {{
            display: inline-block;
            background: #EDF2F7;
            color: #1B2A4A !important;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.01em;
            padding: 0.2rem 0.68rem;
            border-radius: 6px;
            margin-right: 0.4rem;
        }}
        .hq-guide-bar {{
            background: #FFFFFF;
            border: 1px solid #E5E0D5;
            border-left: 4px solid #0D9488;
            border-radius: 12px;
            padding: 1rem 1.35rem;
            margin-bottom: 1.35rem;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}
        .hq-section-label {{
            font-size: 0.78rem;
            font-weight: 700;
            color: #0D9488 !important;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }}
        @keyframes hqPopIn {{
            0% {{ opacity: 0; transform: translateY(-4px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        .hq-award-banner {{
            background: #F4FBF9;
            border: 1.5px solid #0D9488;
            border-radius: 12px;
            padding: 0.9rem 1.25rem;
            margin-bottom: 1.1rem;
            animation: hqPopIn 0.25s ease-out 1;
        }}
        @media (max-width: 768px) {{
            .block-container {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}
            .hq-card, .hq-card-selected {{
                padding: 1.15rem;
            }}
            .hq-scenario-card {{
                min-height: auto;
            }}
            div.stButton > button {{
                width: 100% !important;
            }}
        }}
        {motion_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_simple_guide(now_do: str, why_do: str):
    """학생이 지금 할 일과 학습 이유를 차분하고 세련되게 안내하는 가이드 바."""
    st.markdown(
        f"""
        <div class="hq-guide-bar">
            <div style="font-size:0.97rem;">
                <span class="hq-badge-teal">학습 안내</span>
                <strong style="color:#14223D;">{now_do}</strong>
            </div>
            <div style="font-size:0.88rem; color:#475569; padding-left:0.2rem;">
                학습 목적 · {why_do}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_one_time_notifications():
    """새 배지 획득 또는 미션 3개 완료 시 1회성 안내 배너."""
    badge = st.session_state.pop("hq_pending_badge_notice", None)
    if badge:
        st.markdown(
            f"""
            <div class="hq-award-banner">
                <span class="hq-badge-teal">역량 달성</span>
                <strong style="color:#14223D;">{badge['title']}</strong> — {badge['desc']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    celeb = st.session_state.pop("hq_pending_celebration", None)
    if celeb:
        if not st.session_state.get("hq_reduce_motion", False):
            st.balloons()
        st.markdown(
            """
            <div class="hq-award-banner" style="border-color:#E05A47; background:#FFFDFB;">
                <span class="hq-badge-coral">실습 미션 완주</span>
                <strong style="color:#14223D;">선택한 실습 상황의 3단계 미션을 모두 해결했습니다. [STEP 04 · 활동지 완성]으로 이동해 결과를 정리해 보세요.</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# STEP 01: 오늘의 미션 (좌우 균형 잡힌 대시보드)
# =========================================================
def render_home_dashboard():
    scenario = get_current_scenario_data()
    completed, total, ratio = get_scenario_progress(scenario)
    active_idx = st.session_state.get("hq_active_mission_idx", 0)
    current_mission = scenario["missions"][min(active_idx, len(scenario["missions"]) - 1)]
    earned_badges = st.session_state.get("hq_earned_badges", [])
    xp = st.session_state.get("hq_xp", 0)

    render_simple_guide(
        now_do="오늘의 실습 주제와 학습 목표를 확인하고 [미션 시작하기] 버튼을 눌러 학습을 시작하세요.",
        why_do="3~5분 분량의 병원 현장 사례를 단계별로 해결하며 환자를 안전하게 돌보는 임상 추론 역량을 기릅니다.",
    )

    col_left, col_right = st.columns([1.25, 1], gap="large")

    with col_left:
        st.markdown(
            f"""
            <div class="hq-card-selected" style="min-height: 250px; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div style="margin-bottom:0.75rem;">
                        <span class="hq-badge-teal">오늘의 실습 과제</span>
                        <span class="hq-badge-navy">예상 소요시간 3~5분</span>
                    </div>
                    <h3 style="margin:0.15rem 0 0.65rem 0; font-size:1.3rem;">{scenario['title']}</h3>
                    <p style="font-size:0.95rem; color:#334155; margin-bottom:1.1rem;">
                        {scenario['summary']}
                    </p>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:0.9rem 1.1rem; font-size:0.92rem;">
                    <strong style="color:#0F766E;">이번 단계 학습 목표</strong><br>
                    <span style="color:#1B2A4A;">{current_mission['learning_objective']}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2, gap="small")
        with c1:
            start_label = "미션 이어하기" if completed > 0 else "미션 시작하기"
            if st.button(start_label, type="primary", use_container_width=True, key="home_start_btn"):
                st.session_state["hq_nav_view"] = "STEP 03 · 미션 수행"
                st.rerun()
        with c2:
            if st.button("다른 실습 상황 살펴보기", type="secondary", use_container_width=True, key="home_pick_btn"):
                st.session_state["hq_nav_view"] = "STEP 02 · 상황 선택"
                st.rerun()

    with col_right:
        badge_names = [BADGE_DEFINITIONS[b]["title"] for b in earned_badges if b in BADGE_DEFINITIONS]
        badge_html = (
            " · ".join([f"<span class='hq-badge-teal' style='margin-bottom:4px;'>{name}</span>" for name in badge_names])
            if badge_names
            else "<span style='color:#64748B; font-size:0.9rem;'>미션을 수행하고 판단 근거를 작성하면 역량 배지가 기록됩니다.</span>"
        )
        st.markdown(
            f"""
            <div class="hq-card" style="min-height: 250px; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div class="hq-section-label">MY PROGRESS</div>
                    <h4 style="margin:0 0 0.9rem 0; font-size:1.12rem;">나의 학습 현황</h4>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
                        <div style="background:#FAF8F5; border:1px solid #E5E0D5; border-radius:10px; padding:0.75rem 0.9rem;">
                            <div style="font-size:0.8rem; color:#64748B;">완료한 미션</div>
                            <div style="font-size:1.25rem; font-weight:700; color:#14223D;">{completed} / {total} <span style="font-size:0.85rem; font-weight:500; color:#0F766E;">({int(ratio * 100)}%)</span></div>
                        </div>
                        <div style="background:#FAF8F5; border:1px solid #E5E0D5; border-radius:10px; padding:0.75rem 0.9rem;">
                            <div style="font-size:0.8rem; color:#64748B;">누적 성취도</div>
                            <div style="font-size:1.25rem; font-weight:700; color:#14223D;">{xp} <span style="font-size:0.85rem; font-weight:500; color:#475569;">점</span></div>
                        </div>
                    </div>
                </div>
                <div style="background:#F8FAFC; padding:0.8rem 0.95rem; border-radius:10px; border:1px solid #E2E8F0;">
                    <div style="font-size:0.82rem; font-weight:600; color:#475569; margin-bottom:0.35rem;">달성한 간호 역량</div>
                    <div>{badge_html}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(ratio, text=f"현재 실습 진행률 {int(ratio * 100)}%")


# =========================================================
# STEP 02: 핵심 용어 확인 & 가상 실습 상황 3개 중 1개 선택
# =========================================================
def render_unit_inquiry_and_scenario_selection():
    unit = get_current_unit_data()
    current_scen = get_current_scenario_data()

    render_simple_guide(
        now_do="주요 의학용어의 개념을 살펴본 뒤, 오늘 도전할 가상 실습 상황(A·B·C) 중 1개를 선택하세요.",
        why_do="핵심 개념을 먼저 이해하고 스스로 실습 상황을 선택하면 임상 문제의 단서를 훨씬 정확하게 파악할 수 있습니다.",
    )

    st.markdown("<div class='hq-section-label'>PART 01 · KEY CONCEPTS</div>", unsafe_allow_html=True)
    st.subheader("핵심 의학용어 빠르게 확인하기")

    term_items = list(unit["key_terms"].items())
    if "hq_selected_term_idx" not in st.session_state:
        st.session_state["hq_selected_term_idx"] = 0

    t_cols = st.columns(len(term_items), gap="small")
    for i, (t_name, _) in enumerate(term_items):
        short_name = t_name.split("(")[0].strip()
        is_active_term = st.session_state.get("hq_selected_term_idx", 0) == i
        with t_cols[i]:
            if st.button(
                short_name,
                key=f"term_btn_{i}",
                type="primary" if is_active_term else "secondary",
                use_container_width=True,
            ):
                st.session_state["hq_selected_term_idx"] = i
                st.rerun()

    sel_t_idx = min(st.session_state.get("hq_selected_term_idx", 0), len(term_items) - 1)
    sel_t_name, sel_t_desc = term_items[sel_t_idx]
    st.markdown(
        f"""
        <div class="hq-card" style="background:#F8FAFC; border-color:#CBD5E1; padding:1.1rem 1.4rem; margin-top:0.2rem;">
            <span class="hq-badge-teal">개념 설명</span>
            <strong style="font-size:1.02rem; color:#14223D;">{sel_t_name}</strong>
            <p style="font-size:0.95rem; color:#334155; margin:0.45rem 0 0 0;">{sel_t_desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("궁금한 개념이나 의학용어 직접 질문하기"):
        st.caption("※ 실제 환자 실명이나 학생 개인의 건강정보는 입력하지 마세요.")
        with st.form("simple_q_form", clear_on_submit=False):
            q_input = st.text_input(
                "이 단원에서 더 알고 싶은 개념을 한 문장으로 적어보세요",
                placeholder="예: 비말주의와 접촉주의는 보호구 착용에서 어떤 차이가 있나요?",
            )
            q_sub = st.form_submit_button("질문 등록 및 튜터 설명 보기", type="primary")
        if q_sub and q_input.strip():
            generate_unit_inquiry_feedback(unit, q_input, "고2 눈높이")
            st.rerun()
        if st.session_state["hq_unit_questions"]:
            last_q = st.session_state["hq_unit_questions"][-1]
            st.info(f"**나의 질문**: {last_q['question']}\n\n{last_q['feedback_markdown']}")

    st.markdown("<hr style='margin: 1.5rem 0; border-color: #E5E0D5;'>", unsafe_allow_html=True)

    st.markdown("<div class='hq-section-label'>PART 02 · SCENARIO SELECTION</div>", unsafe_allow_html=True)
    st.subheader("가상 실습 상황 3개 중 1개 선택하기")

    scen_cols = st.columns(3, gap="medium")
    for idx, scen in enumerate(unit["scenarios"]):
        is_selected = scen["scenario_id"] == current_scen["scenario_id"]
        c_done, c_total, _ = get_scenario_progress(scen)
        card_class = "hq-card-selected" if is_selected else "hq-card"

        with scen_cols[idx]:
            st.markdown(
                f"""
                <div class="{card_class} hq-scenario-card">
                    <div>
                        <div style="margin-bottom:0.55rem;">
                            <span class="hq-badge-teal">실습 상황 {scen['code']}</span>
                            <span class="hq-badge-navy">{scen['difficulty']}</span>
                        </div>
                        <h4 style="margin:0.2rem 0 0.55rem 0; font-size:1.05rem;">{scen['title']}</h4>
                        <p style="font-size:0.9rem; color:#475569; margin-bottom:0.8rem;">{scen['summary']}</p>
                    </div>
                    <div style="font-size:0.84rem; color:#0F766E; font-weight:600; border-top:1px solid #F1F5F9; padding-top:0.55rem;">
                        완료한 미션: {c_done} / {c_total}단계
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            btn_label = f"상황 {scen['code']} 선택 및 시작" if not is_selected else f"상황 {scen['code']} 진행 중 (이어하기)"
            if st.button(
                btn_label,
                key=f"pick_scen_{scen['scenario_id']}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state["hq_selected_scenario_id"] = scen["scenario_id"]
                st.session_state["hq_active_mission_idx"] = 0
                st.session_state["hq_nav_view"] = "STEP 03 · 미션 수행"
                st.rerun()


# =========================================================
# STEP 03: 미션 수행 (상황 확인 → 판단 및 근거 작성 → 피드백)
# =========================================================
def render_mission_runner():
    scenario = get_current_scenario_data()
    missions = scenario["missions"]
    active_idx = min(st.session_state.get("hq_active_mission_idx", 0), len(missions) - 1)
    mission = missions[active_idx]
    m_id = mission["id"]
    existing_sub = st.session_state["hq_submissions"].get(m_id)
    existing_ref = st.session_state["hq_reflections"].get(m_id, "")

    render_simple_guide(
        now_do=f"[미션 0{mission['step_num']}] 환자 상황과 단서를 읽고 가장 적절한 간호 행동을 선택한 뒤, 판단 이유를 한 문장으로 작성해 제출하세요.",
        why_do=mission["learning_objective"],
    )

    m_cols = st.columns(len(missions), gap="small")
    for i, m_item in enumerate(missions):
        sub_i = st.session_state["hq_submissions"].get(m_item["id"])
        is_cleared = bool(sub_i and sub_i.get("is_correct") and len(sub_i.get("rationale", "")) >= 5)
        status_mark = " (완료)" if is_cleared else ""
        step_kind = "개념 확인" if i == 0 else "상황 판단"
        with m_cols[i]:
            if st.button(
                f"미션 0{m_item['step_num']} · {step_kind}{status_mark}",
                key=f"step_m_{m_item['id']}",
                type="primary" if i == active_idx else "secondary",
                use_container_width=True,
            ):
                st.session_state["hq_active_mission_idx"] = i
                st.rerun()

    clues_html = " &nbsp;·&nbsp; ".join([f"<strong>{c}</strong>" for c in mission["clinical_clues"]])
    st.markdown(
        f"""
        <div class="hq-card" style="margin-top:0.35rem;">
            <div style="margin-bottom:0.55rem;">
                <span class="hq-badge-teal">미션 0{mission['step_num']} / 0{len(missions)}</span>
                <span class="hq-badge-coral">{mission['question_type']}</span>
            </div>
            <h3 style="margin:0.15rem 0 0.75rem 0; font-size:1.25rem;">{mission['title']}</h3>
            <div style="font-size:0.98rem; background:#FAF8F5; padding:1.05rem 1.25rem; border-radius:10px; border:1px solid #E5E0D5; margin-bottom:0.75rem;">
                <strong style="color:#14223D;">현장 상황</strong><br>
                <span style="color:#1B2A4A;">{mission['situation']}</span>
            </div>
            <div style="font-size:0.91rem; background:#F4FBF9; padding:0.75rem 1.1rem; border-radius:10px; border:1px solid #CCFBF1; color:#0F766E;">
                <strong>관찰된 핵심 단서</strong> &nbsp;|&nbsp; {clues_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("판단이 어려울 때 참고 힌트 열기"):
        st.info(mission["hint"])

    default_idx = existing_sub["selected_idx"] if existing_sub else 0
    default_rationale = existing_sub["rationale"] if existing_sub else ""

    with st.form(key=f"form_{m_id}", clear_on_submit=False):
        st.markdown(f"#### 질문. {mission['question']}")
        selected_option = st.radio(
            "가장 적절한 간호 판단 선택지 (1개 선택)",
            options=list(range(len(mission["options"]))),
            format_func=lambda idx: f"{idx + 1}번. {mission['options'][idx]}",
            index=default_idx,
            key=f"radio_{m_id}",
        )
        rationale_input = st.text_input(
            "위와 같이 판단한 이유(근거)를 한 문장으로 작성해 보세요",
            value=default_rationale,
            placeholder="예: 분비물 노출 가능성이 있으므로 흐르는 물과 비누로 충분히 손을 씻어야 교차감염을 예방할 수 있습니다.",
            key=f"rat_{m_id}",
        )
        btn_txt = "수정한 내용으로 다시 제출하기" if existing_sub else "판단 및 근거 제출하기"
        submitted = st.form_submit_button(btn_txt, type="primary", use_container_width=True)

    if submitted:
        evaluate_mission_submission(mission, selected_option, rationale_input)
        st.rerun()

    sub = st.session_state["hq_submissions"].get(m_id)
    if sub:
        if sub["is_correct"]:
            st.markdown(
                f"""
                <div class="hq-card-selected">
                    <span class="hq-badge-teal">올바른 임상 판단</span>
                    <h4 style="margin:0.4rem 0; color:#0F766E;">정확한 판단입니다 ({sub['selected_idx'] + 1}번 선택)</h4>
                    <p style="font-size:0.95rem; margin-bottom:0.55rem;">
                        <strong>해설</strong> · {mission['option_explanations'][sub['selected_idx']]}
                    </p>
                    <div style="font-size:0.89rem; background:#F8FAFC; padding:0.75rem 1rem; border-radius:8px; border:1px solid #E2E8F0;">
                        <strong>작성한 판단 근거</strong>: "{html.escape(sub['rationale']) if sub['rationale'] else '(판단 이유를 한 문장으로 덧붙이면 근거 추론 역량이 기록됩니다.)'}"
                        <br><span style="color:#0F766E; font-weight:600;">평가 안내 · {sub['rationale_status']}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="hq-card-coral">
                    <span class="hq-badge-coral">재검토 안내 (감점 없음)</span>
                    <h4 style="margin:0.4rem 0; color:#14223D;">놓친 임상 단서를 확인하고 다시 판단해 보세요</h4>
                    <p style="font-size:0.93rem; margin-bottom:0.5rem;">
                        <strong>선택한 보기 피드백</strong> · {mission['option_explanations'][sub['selected_idx']]}
                    </p>
                    <div style="font-size:0.92rem; background:#FFFFFF; padding:0.8rem 1rem; border-radius:8px; border:1px solid #F3DCD8;">
                        <strong style="color:#C0392B;">다시 생각할 단서</strong> · {mission['missed_clue_guide']}<br>
                        <span style="color:#475569; font-size:0.88rem;">위 선택창에서 다시 판단을 고르고 [수정한 내용으로 다시 제출하기]를 눌러보세요.</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("전체 선택지(1~4번) 상세 해설 및 근거 출처 확인하기"):
            for idx, exp_text in enumerate(mission["option_explanations"]):
                prefix = "[정답] " if idx == mission["correct_index"] else f"[{idx + 1}번] "
                st.markdown(f"**{prefix}{mission['options'][idx]}**\n  - {exp_text}")
            st.caption(f"참고 출처: {mission['reference_source']} | 검토 상태: {mission['review_status']}")

        with st.form(key=f"ref_form_{m_id}", clear_on_submit=False):
            ref_val = st.text_input(
                f"성찰 기록 · {mission['reflection_prompt']}",
                value=existing_ref,
                placeholder="이번 미션을 통해 알게 된 핵심 원칙이나 다짐을 한 줄로 적어보세요.",
            )
            ref_saved = st.form_submit_button("성찰 기록 저장하기", type="secondary")
        if ref_saved and ref_val.strip():
            save_mission_reflection(mission, ref_val)
            st.toast("성찰 기록이 저장되었습니다.")
            st.rerun()

        if active_idx < len(missions) - 1:
            if st.button(f"다음 단계 (미션 0{active_idx + 2})로 이동하기", type="primary", use_container_width=True):
                st.session_state["hq_active_mission_idx"] = active_idx + 1
                st.rerun()
        else:
            if st.button("미션 3단계 완료 · [STEP 04 · 활동지 완성]으로 이동하기", type="primary", use_container_width=True):
                st.session_state["hq_nav_view"] = "STEP 04 · 활동지 완성"
                st.rerun()


# =========================================================
# STEP 04: 모둠 토의 정리 & 수업 활동지 저장·인쇄
# =========================================================
def _build_printable_activity_sheet_html(student_name: str, group_name: str) -> str:
    """학생이 바로 인쇄하거나 파일로 제출할 수 있는 정돈된 A4 스타일 수업 활동지 생성."""
    unit_name = st.session_state.get("hq_selected_unit", "")
    scenario = get_current_scenario_data()
    completed, total, _ = get_scenario_progress(scenario)
    xp = st.session_state.get("hq_xp", 0)
    earned = [BADGE_DEFINITIONS[b]["title"] for b in st.session_state.get("hq_earned_badges", []) if b in BADGE_DEFINITIONS]
    notes = st.session_state.get("hq_team_notes", {})

    rows_html = ""
    for m in scenario["missions"]:
        sub = st.session_state["hq_submissions"].get(m["id"])
        ref = st.session_state["hq_reflections"].get(m["id"], "-")
        if sub:
            choice_str = f"{sub['selected_idx'] + 1}번. {html.escape(sub['selected_text'])}"
            status_str = "완료" if sub["is_correct"] else "재도전 중"
            rat_str = html.escape(sub["rationale"]) if sub["rationale"] else "-"
        else:
            choice_str = "(미작성)"
            status_str = "미제출"
            rat_str = "-"

        rows_html += f"""
        <tr>
            <td style="font-weight:600; text-align:center;">미션 0{m['step_num']}<br><span style="font-size:12px;color:#0F766E;">({status_str})</span></td>
            <td><strong>{html.escape(m['title'])}</strong><br><span style="font-size:13px; color:#334155;">선택: {choice_str}</span></td>
            <td>{rat_str}</td>
            <td>{html.escape(ref)}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>보건간호 PBL 수업 활동지</title>
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    body {{
        font-family: 'Pretendard', 'Malgun Gothic', sans-serif;
        color: #1B2A4A;
        background: #FFFFFF;
        margin: 20px;
        line-height: 1.6;
        letter-spacing: -0.015em;
        word-break: keep-all;
    }}
    .sheet-box {{
        max-width: 840px;
        margin: 0 auto;
        border: 1.5px solid #CBD5E1;
        border-top: 5px solid #0D9488;
        border-radius: 12px;
        padding: 28px 32px;
    }}
    .header-row {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 1.5px solid #E2E8F0;
        padding-bottom: 12px;
        margin-bottom: 16px;
    }}
    h1 {{ margin: 0; font-size: 21px; color: #14223D; letter-spacing: -0.02em; }}
    .sub-caption {{ font-size: 13px; color: #64748B; margin-top: 4px; }}
    .meta-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px 20px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 20px;
        font-size: 13.5px;
    }}
    h2 {{
        font-size: 15.5px;
        color: #0F766E;
        margin: 22px 0 8px 0;
        padding-left: 8px;
        border-left: 3px solid #0D9488;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    th, td {{ border: 1px solid #CBD5E1; padding: 10px 12px; text-align: left; vertical-align: top; }}
    th {{ background: #F1F5F9; color: #14223D; font-weight: 600; }}
    .team-box {{
        background: #FAF8F5;
        border: 1px solid #E5E0D5;
        border-radius: 8px;
        padding: 14px 18px;
        font-size: 13.5px;
    }}
    .team-box p {{ margin: 6px 0; }}
    .print-btn {{
        background: #0D9488;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 9px 16px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
    }}
    @media print {{ .no-print {{ display: none !important; }} body {{ margin: 0; }} .sheet-box {{ border: 1px solid #94A3B8; }} }}
</style>
</head>
<body>
<div class="sheet-box">
    <div class="header-row">
        <div>
            <h1>{html.escape(SITE_CONFIG['site_title'])} — 수업 결과 활동지</h1>
            <div class="sub-caption">특성화고등학교 보건간호과 임상 추론 및 협력적 문제해결(PBL) 기록표</div>
        </div>
        <div class="no-print">
            <button class="print-btn" onclick="window.print()">인쇄 또는 PDF로 저장하기</button>
        </div>
    </div>

    <div class="meta-grid">
        <div><strong>학번 / 이름</strong>: {html.escape(student_name or '미입력')}</div>
        <div><strong>모둠명</strong>: {html.escape(group_name or '미입력')}</div>
        <div><strong>실습 단원</strong>: {html.escape(unit_name)}</div>
        <div><strong>실습 상황</strong>: {html.escape(scenario['title'])}</div>
        <div><strong>미션 달성도</strong>: {completed} / {total}단계 완료 ({xp}점)</div>
        <div><strong>달성 역량</strong>: {html.escape(', '.join(earned) if earned else '진행 중')}</div>
    </div>

    <h2>1. 단계별 임상 판단 및 근거 기록</h2>
    <table>
        <thead>
            <tr>
                <th style="width:13%; text-align:center;">단계</th>
                <th style="width:33%;">미션 주제 및 선택한 행동</th>
                <th style="width:30%;">작성한 임상적 판단 근거</th>
                <th style="width:24%;">성찰 기록</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <h2>2. 모둠원 근거 비교 및 공동 해결안</h2>
    <div class="team-box">
        <p><strong>1) 모둠원과 비교한 생각의 차이</strong>: {html.escape(notes.get('peer_comparison') or '-')}</p>
        <p><strong>2) 우리 모둠의 최종 해결 방안과 핵심 근거</strong>: {html.escape(notes.get('team_conclusion') or '-')}</p>
        <p><strong>3) 토의 후 새롭게 깨닫거나 보완한 점</strong>: {html.escape(notes.get('thought_change') or '-')}</p>
    </div>
</div>
</body>
</html>"""


def render_collaboration_and_growth():
    scenario = get_current_scenario_data()

    render_simple_guide(
        now_do="모둠 친구와 판단 근거를 비교하여 아래 3가지 항목을 작성한 뒤, 완성된 수업 활동지를 인쇄하거나 파일로 저장하세요.",
        why_do="개인의 판단을 모둠원의 시각과 비교하며 더 안전한 간호 우선순위를 도출하고, 한 장의 활동지로 정리해 제출할 수 있습니다.",
    )

    notes = st.session_state.get("hq_team_notes", {})
    student_name = st.session_state.get("hq_student_label", "")
    group_name = st.session_state.get("hq_group_label", "")

    st.markdown("<div class='hq-section-label'>PART 01 · TEAM COLLABORATION</div>", unsafe_allow_html=True)
    st.subheader("모둠 토의 및 공동 해결안 정리")

    with st.form("simple_team_form", clear_on_submit=False):
        c_info1, c_info2 = st.columns(2, gap="medium")
        with c_info1:
            s_name_in = st.text_input("학번 및 이름 (활동지 기재용)", value=student_name, placeholder="예: 2학년 1반 홍길동")
        with c_info2:
            g_name_in = st.text_input("모둠 이름 (선택)", value=group_name, placeholder="예: 환자안전 1모둠")

        peer_comp = st.text_input(
            "1. 모둠 친구의 판단 근거와 내 생각은 어떤 점이 같거나 달랐나요?",
            value=notes.get("peer_comparison", ""),
            placeholder="예: 나는 손 위생 시간만 생각했는데, 친구는 환자 간 거리 확보까지 함께 제시해 주었다.",
        )
        team_conc = st.text_input(
            "2. 우리 모둠이 합의한 '최우선 안전 간호 행동'과 그 이유는 무엇인가요?",
            value=notes.get("team_conclusion", ""),
            placeholder="예: 보호구 착용과 손 위생을 가장 먼저 시행해야 병원 내 교차감염 경로를 확실히 차단할 수 있다.",
        )
        thought_chg = st.text_input(
            "3. 모둠 토의를 마치고 새롭게 알게 되었거나 바뀐 생각을 한 줄로 적어보세요.",
            value=notes.get("thought_change", ""),
            placeholder="예: 응급 상황일수록 기본 보호구 착용과 폐기물 처리 원칙을 생략하지 않아야 한다는 점을 깨달았다.",
        )
        save_btn = st.form_submit_button("작성 내용 반영하여 수업 활동지 완성하기", type="primary", use_container_width=True)

    if save_btn:
        st.session_state["hq_student_label"] = s_name_in.strip()
        st.session_state["hq_group_label"] = g_name_in.strip()
        st.session_state["hq_team_notes"] = {
            "peer_comparison": peer_comp.strip(),
            "team_conclusion": team_conc.strip(),
            "team_rationale": team_conc.strip(),
            "thought_change": thought_chg.strip(),
            "saved_at": "저장 완료",
        }
        if team_conc.strip():
            award_action_once(
                action_key=f"team_collab:{scenario['scenario_id']}",
                action_type="모둠 정리 완료",
                label=f"[{scenario['title']}] 모둠 토의 및 활동지 작성 완료",
                xp_gain=40,
                badge_id="team_collaborator",
            )
        st.success("수업 활동지가 업데이트되었습니다. 아래 미리보기에서 인쇄하거나 파일로 저장해 제출하세요.")
        st.rerun()

    st.markdown("<hr style='margin: 1.6rem 0; border-color: #E5E0D5;'>", unsafe_allow_html=True)

    st.markdown("<div class='hq-section-label'>PART 02 · ACTIVITY SHEET EXPORT</div>", unsafe_allow_html=True)
    st.subheader("완성된 수업 활동지 확인 및 제출용 저장")
    st.caption("※ 브라우저 창을 닫거나 새로고침하면 현재 작성 내용이 초기화될 수 있으므로, 작성 후 아래 버튼으로 활동지를 저장하거나 인쇄해 두세요.")

    sheet_html = _build_printable_activity_sheet_html(
        st.session_state.get("hq_student_label", ""),
        st.session_state.get("hq_group_label", ""),
    )

    btn_col1, btn_col2 = st.columns(2, gap="medium")
    with btn_col1:
        st.download_button(
            label="제출용 수업 활동지 파일 내려받기",
            data=sheet_html,
            file_name="보건간호_미션_수업활동지.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )
    with btn_col2:
        simple_txt = (
            f"[{SITE_CONFIG['site_title']} - 수업 결과 요약]\n"
            f"학번/이름: {st.session_state.get('hq_student_label', '미입력')} | 모둠: {st.session_state.get('hq_group_label', '미입력')}\n"
            f"실습 상황: {scenario['title']}\n\n"
            f"1) 모둠원과 비교한 생각 차이: {st.session_state['hq_team_notes'].get('peer_comparison', '-')}\n"
            f"2) 우리 모둠 최종 결론과 근거: {st.session_state['hq_team_notes'].get('team_conclusion', '-')}\n"
            f"3) 토의 후 새롭게 깨달은 점: {st.session_state['hq_team_notes'].get('thought_change', '-')}\n"
        )
        st.download_button(
            label="간단 요약문 파일로 내려받기",
            data=simple_txt,
            file_name="보건간호_미션_수업요약.txt",
            mime="text/plain",
            use_container_width=True,
        )

    components.html(sheet_html, height=640, scrolling=True)
