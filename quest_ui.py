"""HEALTH QUEST — 예비 보건의료인의 미션룸: 직관적 단계별(Step-by-Step) UI·UX 및 활동지 출력 모듈."""
import html
import streamlit as st
import streamlit.components.v1 as components
from quest_data import SITE_CONFIG, UNIT_CATALOG
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
    """밝은 아이보리 배경(#FAF8F5), 딥 네이비 본문(#1B2A4A), 청록색 주요 버튼(#0D9488), 코랄 포인트(#E05A47)."""
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
        :root {{
            color-scheme: light !important;
        }}
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: #FAF8F5 !important;
            color: #1B2A4A !important;
            overflow-x: hidden !important;
        }}
        header[data-testid="stHeader"] {{
            background-color: #FAF8F5 !important;
            color: #1B2A4A !important;
            border-bottom: 1px solid #E5E0D5;
        }}
        .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown {{
            color: #1B2A4A !important;
            line-height: 1.65;
            word-break: keep-all;
            overflow-wrap: break-word;
        }}
        h1, h2, h3, h4 {{
            color: #14223D !important;
            letter-spacing: -0.02em;
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
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 12px !important;
            -webkit-text-fill-color: #1B2A4A !important;
            caret-color: #0D9488 !important;
            font-size: 0.96rem !important;
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
            border: 1.5px solid #E5E0D5 !important;
            border-radius: 16px !important;
            padding: 1.3rem !important;
            box-shadow: 0 2px 8px rgba(27, 42, 74, 0.04);
        }}
        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
            border-color: #E5E0D5 !important;
            border-radius: 12px !important;
        }}
        div[role="radiogroup"] label > div:first-child {{
            background-color: #FFFFFF !important;
            border: 2px solid #0D9488 !important;
        }}
        section[data-testid="stSidebar"] {{
            background-color: #F2EFE9 !important;
            border-right: 1px solid #E2DDD3;
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
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 0.98rem !important;
            padding: 0.65rem 1.2rem !important;
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
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            padding: 0.6rem 1rem !important;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            background-color: #F0FDFA !important;
            border-color: #0D9488 !important;
        }}
        /* 심플 카드 레이아웃 */
        .hq-card {{
            background: #FFFFFF;
            border: 1.5px solid #E5E0D5;
            border-radius: 16px;
            padding: 1.35rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 3px 10px rgba(27, 42, 74, 0.04);
        }}
        .hq-card-selected {{
            background: #F0FDFA;
            border: 2px solid #0D9488;
            border-radius: 16px;
            padding: 1.35rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 14px rgba(13, 148, 136, 0.10);
        }}
        .hq-card-coral {{
            background: #FFFDFB;
            border-left: 5px solid #E05A47;
            border-top: 1px solid #F3DCD8;
            border-right: 1px solid #F3DCD8;
            border-bottom: 1px solid #F3DCD8;
            border-radius: 14px;
            padding: 1.1rem 1.35rem;
            margin-bottom: 1rem;
        }}
        .hq-badge-teal {{
            display: inline-block;
            background: #CCFBF1;
            color: #0F766E !important;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.22rem 0.7rem;
            border-radius: 999px;
            margin-right: 0.4rem;
        }}
        .hq-badge-coral {{
            display: inline-block;
            background: #FEE2E2;
            color: #B91C1C !important;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.22rem 0.7rem;
            border-radius: 999px;
            margin-right: 0.4rem;
        }}
        .hq-badge-navy {{
            display: inline-block;
            background: #E2E8F0;
            color: #1B2A4A !important;
            font-size: 0.82rem;
            font-weight: 700;
            padding: 0.22rem 0.7rem;
            border-radius: 999px;
            margin-right: 0.4rem;
        }}
        .hq-guide-bar {{
            background: #FFFFFF;
            border-left: 5px solid #0D9488;
            border-top: 1px solid #E5E0D5;
            border-right: 1px solid #E5E0D5;
            border-bottom: 1px solid #E5E0D5;
            border-radius: 12px;
            padding: 0.85rem 1.2rem;
            margin-bottom: 1.1rem;
            font-size: 0.98rem;
        }}
        @keyframes hqPopIn {{
            0% {{ opacity: 0; transform: translateY(-5px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        .hq-award-banner {{
            background: #F0FDFA;
            border: 2px solid #0D9488;
            border-radius: 14px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 1rem;
            animation: hqPopIn 0.25s ease-out 1;
        }}
        @media (max-width: 768px) {{
            .hq-card, .hq-card-selected {{
                padding: 1.05rem;
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
    """중학생도 한눈에 읽을 수 있는 2줄 핵심 안내 바."""
    st.markdown(
        f"""
        <div class="hq-guide-bar">
            <div><span class="hq-badge-teal">지금 할 일</span> <b>{now_do}</b></div>
            <div style="font-size:0.88rem; color:#475569; margin-top:0.25rem;">💡 <b>왜 필요할까요?</b> {why_do}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_one_time_notifications():
    """새 배지 획득 또는 미션 3개 완료 시 1회성 축하 배너."""
    badge = st.session_state.pop("hq_pending_badge_notice", None)
    if badge:
        st.markdown(
            f"""
            <div class="hq-award-banner">
                <span class="hq-badge-teal">새 배지 획득!</span>
                <b>🏅 {badge['title']}</b> — {badge['desc']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    celeb = st.session_state.pop("hq_pending_celebration", None)
    if celeb:
        if not st.session_state.get("hq_reduce_motion", False):
            st.balloons()
        st.markdown(
            f"""
            <div class="hq-award-banner" style="border-color:#E05A47;">
                <span class="hq-badge-coral">미션 3개 모두 클리어!</span>
                <b>🎉 축하합니다! 오늘 실습 미션을 모두 해결했어요. 이제 [4단계: 활동지 저장·인쇄]로 이동해 보세요!</b>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 1단계: 미션룸 홈 (심플한 시작 화면)
# =========================================================
def render_home_dashboard():
    scenario = get_current_scenario_data()
    completed, total, ratio = get_scenario_progress(scenario)
    active_idx = st.session_state.get("hq_active_mission_idx", 0)
    current_mission = scenario["missions"][min(active_idx, len(scenario["missions"]) - 1)]
    earned_badges = st.session_state.get("hq_earned_badges", [])
    xp = st.session_state.get("hq_xp", 0)

    render_simple_guide(
        now_do="오늘의 미션 주제를 읽고 아래 [🚀 미션 시작하기] 버튼을 눌러보세요!",
        why_do="짧은 병원 현장 미션(3~5분)을 하나씩 해결하며 환자를 안전하게 돌보는 판단력을 키울 수 있어요.",
    )

    col_left, col_right = st.columns([1.5, 1], gap="medium")

    with col_left:
        st.markdown(
            f"""
            <div class="hq-card-selected">
                <div style="margin-bottom:0.6rem;">
                    <span class="hq-badge-teal">오늘의 실습 주제</span>
                    <span class="hq-badge-navy">⏱ 소요시간 약 3~5분</span>
                </div>
                <h3 style="margin:0.2rem 0 0.6rem 0;">{scenario['title']}</h3>
                <p style="font-size:0.96rem; color:#334155; margin-bottom:0.8rem;">
                    {scenario['summary']}
                </p>
                <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:12px; padding:0.85rem 1rem;">
                    <b>🎯 오늘의 목표</b>: {current_mission['learning_objective']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            start_label = "🚀 미션 이어하기 →" if completed > 0 else "🚀 바로 미션 시작하기 →"
            if st.button(start_label, type="primary", use_container_width=True, key="home_start_btn"):
                st.session_state["hq_nav_view"] = "🩺 3단계: 미션 도전"
                st.rerun()
        with c2:
            if st.button("🧭 다른 실습 상황 고르기 (3가지)", type="secondary", use_container_width=True, key="home_pick_btn"):
                st.session_state["hq_nav_view"] = "🧭 2단계: 상황 고르기"
                st.rerun()

    with col_right:
        badge_names = [f"🏅 {BADGE_DEFINITIONS[b]['title']}" for b in earned_badges if b in BADGE_DEFINITIONS]
        badge_html = " · ".join(badge_names) if badge_names else "아직 획득한 배지가 없어요. 첫 미션에 도전해 보세요!"
        st.markdown(
            f"""
            <div class="hq-card">
                <h4 style="margin-top:0;">🌱 나의 성장 현황</h4>
                <p style="font-size:1.02rem; margin-bottom:0.4rem;">
                    • 해결한 미션: <b>{completed} / {total}개</b> ({int(ratio * 100)}%)<br>
                    • 나의 성장 점수: <b>{xp}점</b>
                </p>
                <div style="font-size:0.88rem; background:#F8FAFC; padding:0.65rem 0.85rem; border-radius:10px; border:1px solid #E2E8F0;">
                    <b>획득한 역량 배지</b><br>{badge_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(ratio, text=f"오늘 미션 달성률 {int(ratio * 100)}%")


# =========================================================
# 2단계: 용어 힌트 & 가상 실습 상황 3개 중 1개 고르기
# =========================================================
def render_unit_inquiry_and_scenario_selection():
    unit = get_current_unit_data()
    current_scen = get_current_scenario_data()

    render_simple_guide(
        now_do="어려운 의학용어를 클릭해 뜻을 확인하고, 오늘 도전할 실습 상황(A·B·C) 중 1개를 골라주세요!",
        why_do="개념을 먼저 이해하고 내가 원하는 병원 상황을 직접 고르면 훨씬 쉽고 재미있게 문제를 해결할 수 있어요.",
    )

    # 1) 클릭하면 바로 뜻이 나오는 심플 의학용어 카드 + 1줄 질문창
    st.subheader("1️⃣ 헷갈리는 의학용어 콕 집어 보기")
    term_items = list(unit["key_terms"].items())
    if "hq_selected_term_idx" not in st.session_state:
        st.session_state["hq_selected_term_idx"] = 0

    t_cols = st.columns(len(term_items))
    for i, (t_name, _) in enumerate(term_items):
        short_name = t_name.split("(")[0].strip()
        is_active_term = st.session_state.get("hq_selected_term_idx", 0) == i
        with t_cols[i]:
            if st.button(
                f"📘 {short_name}",
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
        <div class="hq-card" style="background:#F0FDFA; border-color:#0D9488; padding:1rem 1.25rem;">
            <span class="hq-badge-teal">쉬운 용어 풀이</span> <b>{sel_t_name}</b><br>
            <span style="font-size:0.95rem;">{sel_t_desc}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("💬 AI 보건튜터에게 더 궁금한 점 질문하기 (클릭해서 열기)"):
        st.caption("※ 실제 환자 실명이나 내 개인 건강정보는 적지 마세요.")
        with st.form("simple_q_form", clear_on_submit=False):
            q_input = st.text_input(
                "이 단원에서 궁금한 점을 한 줄로 적어보세요",
                placeholder="예: 비말주의와 접촉주의는 무엇이 다른가요?",
            )
            q_sub = st.form_submit_button("질문하고 답변 보기", type="primary")
        if q_sub and q_input.strip():
            generate_unit_inquiry_feedback(unit, q_input, "고2 눈높이")
            st.rerun()
        if st.session_state["hq_unit_questions"]:
            last_q = st.session_state["hq_unit_questions"][-1]
            st.info(f"**질문**: {last_q['question']}\n\n{last_q['feedback_markdown']}")

    st.markdown("---")

    # 2) 가상 실습 상황 3개(A, B, C) 중 1개 선택 카드 (핵심만 간결하게)
    st.subheader("2️⃣ 오늘 도전할 가상 실습 상황 1개 고르기")
    scen_cols = st.columns(3, gap="medium")
    for idx, scen in enumerate(unit["scenarios"]):
        is_selected = scen["scenario_id"] == current_scen["scenario_id"]
        c_done, c_total, _ = get_scenario_progress(scen)
        card_class = "hq-card-selected" if is_selected else "hq-card"

        with scen_cols[idx]:
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div style="margin-bottom:0.4rem;">
                        <span class="hq-badge-teal">실습 상황 {scen['code']}</span>
                        <span class="hq-badge-navy">난이도: {scen['difficulty']}</span>
                    </div>
                    <h4 style="margin:0.2rem 0 0.5rem 0; font-size:1.05rem;">{scen['title']}</h4>
                    <p style="font-size:0.9rem; color:#334155; margin-bottom:0.6rem;">{scen['summary']}</p>
                    <div style="font-size:0.84rem; color:#0F766E; font-weight:600;">
                        진행 현황: {c_done} / {c_total} 미션 완료
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            btn_label = f"🚀 상황 {scen['code']} 선택하고 미션 시작 →" if not is_selected else f"✔ 상황 {scen['code']}로 미션 도전하기 →"
            if st.button(
                btn_label,
                key=f"pick_scen_{scen['scenario_id']}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state["hq_selected_scenario_id"] = scen["scenario_id"]
                st.session_state["hq_active_mission_idx"] = 0
                st.session_state["hq_nav_view"] = "🩺 3단계: 미션 도전"
                st.rerun()


# =========================================================
# 3단계: 미션 도전 (하나씩 클릭하며 해결하는 깔끔한 구성)
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
        now_do=f"[미션 {mission['step_num']}] 상황을 읽고 알맞은 행동 번호와 그 이유를 한 줄로 적어 제출해 보세요!",
        why_do=mission["learning_objective"],
    )

    # 미션 1 -> 2 -> 3 단계 탭 버튼
    m_cols = st.columns(len(missions))
    for i, m_item in enumerate(missions):
        sub_i = st.session_state["hq_submissions"].get(m_item["id"])
        is_cleared = bool(sub_i and sub_i.get("is_correct") and len(sub_i.get("rationale", "")) >= 5)
        icon = "✅" if is_cleared else f"{i + 1}️⃣"
        with m_cols[i]:
            if st.button(
                f"{icon} 미션 {m_item['step_num']} ({'개념 확인' if i == 0 else '상황 판단'})",
                key=f"step_m_{m_item['id']}",
                type="primary" if i == active_idx else "secondary",
                use_container_width=True,
            ):
                st.session_state["hq_active_mission_idx"] = i
                st.rerun()

    # [카드 1] 현장 상황과 핵심 단서 (한눈에 들어오게 압축)
    clues_html = " · ".join([f"<b>{c}</b>" for c in mission["clinical_clues"]])
    st.markdown(
        f"""
        <div class="hq-card">
            <div style="margin-bottom:0.4rem;">
                <span class="hq-badge-teal">미션 {mission['step_num']} / {len(missions)}</span>
                <span class="hq-badge-coral">{mission['question_type']}</span>
            </div>
            <h3 style="margin:0.2rem 0 0.6rem 0;">{mission['title']}</h3>
            <p style="font-size:1rem; background:#FAF8F5; padding:0.9rem 1.1rem; border-radius:12px; border:1px solid #E5E0D5; margin-bottom:0.6rem;">
                📋 <b>상황</b>: {mission['situation']}
            </p>
            <div style="font-size:0.9rem; background:#F0FDFA; padding:0.65rem 0.95rem; border-radius:10px; color:#0F766E;">
                🔎 <b>핵심 단서</b>: {clues_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("💡 잘 모르겠을 때 힌트 보기 (클릭)"):
        st.info(mission["hint"])

    # [카드 2] 판단 선택 & 이유 한 줄 적기 (제출 전 정답 비공개)
    default_idx = existing_sub["selected_idx"] if existing_sub else 0
    default_rationale = existing_sub["rationale"] if existing_sub else ""

    with st.form(key=f"form_{m_id}", clear_on_submit=False):
        st.markdown(f"**❓ 질문: {mission['question']}**")
        selected_option = st.radio(
            "알맞은 행동을 골라보세요",
            options=list(range(len(mission["options"]))),
            format_func=lambda idx: f"{idx + 1}번. {mission['options'][idx]}",
            index=default_idx,
            key=f"radio_{m_id}",
        )
        rationale_input = st.text_input(
            "✍️ 왜 그렇게 생각했나요? (이유를 한 문장으로 편하게 적어보세요)",
            value=default_rationale,
            placeholder="예: 분비물이 묻었을 가능성이 있어서 물과 비누로 깨끗이 씻어야 안전하기 때문입니다.",
            key=f"rat_{m_id}",
        )
        btn_txt = "🔄 다시 고쳐서 제출하기" if existing_sub else "✅ 제출하고 결과 확인하기"
        submitted = st.form_submit_button(btn_txt, type="primary", use_container_width=True)

    if submitted:
        evaluate_mission_submission(mission, selected_option, rationale_input)
        st.rerun()

    # [카드 3] 제출 후에만 나타나는 심플 결과 & 다음 단계 버튼
    sub = st.session_state["hq_submissions"].get(m_id)
    if sub:
        if sub["is_correct"]:
            st.markdown(
                f"""
                <div class="hq-card-selected">
                    <span class="hq-badge-teal">정답입니다! (+성취 점수 획득)</span>
                    <h4 style="margin:0.35rem 0; color:#0F766E;">🎉 정확한 판단이에요! ({sub['selected_idx'] + 1}번 선택)</h4>
                    <p style="font-size:0.95rem; margin-bottom:0.4rem;">
                        <b>핵심 해설</b>: {mission['option_explanations'][sub['selected_idx']]}
                    </p>
                    <p style="font-size:0.88rem; color:#334155; margin-bottom:0;">
                        📝 <b>내가 적은 이유</b>: "{sub['rationale'] if sub['rationale'] else '(이유를 한 줄 적어보면 배지를 받을 수 있어요!)'}"
                        <br><span style="color:#0F766E;">→ {sub['rationale_status']}</span>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="hq-card-coral">
                    <span class="hq-badge-coral">다시 한번 생각해 볼까요? (감점 없음)</span>
                    <h4 style="margin:0.35rem 0;">🧭 아까워요! 놓친 단서를 확인하고 다시 도전해 보세요</h4>
                    <p style="font-size:0.93rem; margin-bottom:0.4rem;">
                        • <b>방금 고른 보기 설명</b>: {mission['option_explanations'][sub['selected_idx']]}
                    </p>
                    <p style="font-size:0.93rem; background:#FFFFFF; padding:0.7rem 0.9rem; border-radius:10px; margin-bottom:0;">
                        💡 <b>다시 생각할 힌트</b>: {mission['missed_clue_guide']}
                        <br>위에서 다른 번호를 고르고 <b>[🔄 다시 고쳐서 제출하기]</b>를 눌러보세요!
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("📖 1~4번 모든 보기 해설과 참고 출처 보기"):
            for idx, exp_text in enumerate(mission["option_explanations"]):
                prefix = "✅ [정답] " if idx == mission["correct_index"] else f"• [{idx + 1}번] "
                st.markdown(f"**{prefix}{mission['options'][idx]}**\n  - {exp_text}")
            st.caption(f"📚 참고 출처: {mission['reference_source']}")

        # 한 줄 성찰 & 다음 미션 바로가기 버튼
        with st.form(key=f"ref_form_{m_id}", clear_on_submit=False):
            ref_val = st.text_input(
                f"💭 오늘의 한 줄 다짐: {mission['reflection_prompt']}",
                value=existing_ref,
                placeholder="내가 느낀 점을 짧게 한 줄로 적어보세요.",
            )
            ref_saved = st.form_submit_button("💾 한 줄 다짐 저장하기 (+20점)", type="secondary")
        if ref_saved and ref_val.strip():
            save_mission_reflection(mission, ref_val)
            st.toast("한 줄 다짐이 저장되었어요!")
            st.rerun()

        # 다음 미션 이동 버튼 (가장 눈에 띄게!)
        if active_idx < len(missions) - 1:
            if st.button(f"👉 미션 {active_idx + 1} 완료! 다음 [미션 {active_idx + 2}]로 넘어가기 →", type="primary", use_container_width=True):
                st.session_state["hq_active_mission_idx"] = active_idx + 1
                st.rerun()
        else:
            if st.button("🏆 미션 3개 완료! [4단계: 모둠 정리 & 활동지 출력]으로 가기 →", type="primary", use_container_width=True):
                st.session_state["hq_nav_view"] = "🏆 4단계: 활동지 저장·인쇄"
                st.rerun()


# =========================================================
# 4단계: 모둠 정리 & 한눈에 보는 수업 활동지 저장·인쇄
# =========================================================
def _build_printable_activity_sheet_html(student_name: str, group_name: str) -> str:
    """중·고등학생이 바로 인쇄하거나 파일로 열어볼 수 있는 깔끔한 HTML 수업 활동지 생성."""
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
            status_str = "정답 확인 완료" if sub["is_correct"] else "재도전 진행 중"
            rat_str = html.escape(sub["rationale"]) if sub["rationale"] else "-"
        else:
            choice_str = "(미작성)"
            status_str = "미제출"
            rat_str = "-"

        rows_html += f"""
        <tr>
            <td style="font-weight:700;">미션 {m['step_num']}<br><span style="font-size:12px;color:#0F766E;">({status_str})</span></td>
            <td><b>{html.escape(m['title'])}</b><br><span style="font-size:13px;">선택: {choice_str}</span></td>
            <td>{rat_str}</td>
            <td>{html.escape(ref)}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>보건간호 미션 수업 활동지</title>
<style>
    body {{ font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; color: #1B2A4A; background: #FFFFFF; margin: 24px; line-height: 1.55; }}
    .sheet-box {{ max-width: 820px; margin: 0 auto; border: 2px solid #0D9488; border-radius: 14px; padding: 24px 28px; }}
    h1 {{ margin: 0 0 6px 0; font-size: 22px; color: #0F766E; }}
    .meta {{ background: #F0FDFA; border: 1px solid #99F6E4; border-radius: 10px; padding: 12px 16px; margin: 12px 0 18px 0; font-size: 14px; }}
    h2 {{ font-size: 16px; color: #14223D; border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-top: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13.5px; }}
    th, td {{ border: 1px solid #CBD5E1; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #F8FAFC; color: #14223D; }}
    .team-box {{ background: #FAF8F5; border: 1px solid #E5E0D5; border-radius: 10px; padding: 14px 16px; font-size: 14px; }}
    .print-btn {{ background: #0D9488; color: #FFFFFF; border: none; border-radius: 8px; padding: 10px 18px; font-size: 15px; font-weight: 700; cursor: pointer; margin-bottom: 14px; }}
    @media print {{ .no-print {{ display: none !important; }} body {{ margin: 0; }} }}
</style>
</head>
<body>
<div class="sheet-box">
    <div class="no-print" style="text-align:right;">
        <button class="print-btn" onclick="window.print()">🖨️ 지금 바로 인쇄 / PDF로 저장하기</button>
    </div>
    <h1>🩺 {html.escape(SITE_CONFIG['site_title'])} — 수업 결과 활동지</h1>
    <div class="meta">
        <b>• 작성자(이름/학번)</b>: {html.escape(student_name or '미입력')} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>• 모둠명</b>: {html.escape(group_name or '미입력')}<br>
        <b>• 실습 단원</b>: {html.escape(unit_name)} &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>• 선택한 실습 상황</b>: {html.escape(scenario['title'])}<br>
        <b>• 미션 완료 현황</b>: {completed} / {total}개 완료 (성장 점수: {xp}점) &nbsp;&nbsp;|&nbsp;&nbsp;
        <b>• 획득 배지</b>: {html.escape(', '.join(earned) if earned else '도전 중')}
    </div>

    <h2>1. 나의 단계별 미션 판단 및 근거 기록</h2>
    <table>
        <thead>
            <tr>
                <th style="width:14%;">단계</th>
                <th style="width:34%;">미션 주제 및 나의 선택</th>
                <th style="width:28%;">내가 작성한 판단 이유(근거)</th>
                <th style="width:24%;">오늘의 한 줄 다짐(성찰)</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <h2>2. 모둠 친구와 생각 비교 및 공동 해결안</h2>
    <div class="team-box">
        <p style="margin:4px 0;"><b>① 친구와 비교해 본 생각 차이</b>: {html.escape(notes.get('peer_comparison') or '-')}</p>
        <p style="margin:4px 0;"><b>② 우리 모둠이 정한 최종 해결 방법과 이유</b>: {html.escape(notes.get('team_conclusion') or '-')}</p>
        <p style="margin:4px 0;"><b>③ 토의 후 새로 깨닫거나 바뀐 나의 생각</b>: {html.escape(notes.get('thought_change') or '-')}</p>
    </div>
</div>
</body>
</html>"""


def render_collaboration_and_growth():
    scenario = get_current_scenario_data()

    render_simple_guide(
        now_do="모둠 친구와 생각을 비교해 짧은 3칸만 채운 뒤, [🖨️ 수업 활동지 바로 인쇄 / 파일 저장]을 눌러 제출하세요!",
        why_do="내 생각과 친구 생각을 합쳐 정리한 결과가 깔끔한 '수업 활동지' 표로 자동 완성되어 바로 인쇄하거나 제출할 수 있어요.",
    )

    notes = st.session_state.get("hq_team_notes", {})
    student_name = st.session_state.get("hq_student_label", "")
    group_name = st.session_state.get("hq_group_label", "")

    # 1) 심플한 3문항 모둠 정리 폼
    st.subheader("1️⃣ 모둠 토의 3줄 정리하기")
    with st.form("simple_team_form", clear_on_submit=False):
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            s_name_in = st.text_input("이름 또는 학번 (활동지 표시용)", value=student_name, placeholder="예: 2학년 1반 홍길동")
        with c_info2:
            g_name_in = st.text_input("모둠 이름 (선택)", value=group_name, placeholder="예: 나이팅게일 1모둠")

        peer_comp = st.text_input(
            "① 친구의 생각과 내 생각은 어떤 점이 같거나 달랐나요?",
            value=notes.get("peer_comparison", ""),
            placeholder="예: 나는 손 씻기만 생각했는데 친구는 환자 간 거리 두기까지 이야기해 주었다.",
        )
        team_conc = st.text_input(
            "② 우리 모둠이 정한 '가장 중요한 안전 행동 1순위'와 이유는 무엇인가요?",
            value=notes.get("team_conclusion", ""),
            placeholder="예: 마스크 착용과 손 위생을 가장 먼저 해야 감염이 퍼지는 것을 막을 수 있다.",
        )
        thought_chg = st.text_input(
            "③ 오늘 수업을 마치고 새롭게 알게 된 점 한 줄!",
            value=notes.get("thought_change", ""),
            placeholder="예: 바빠도 보호구 착용과 바늘 버리기 원칙을 절대 건너뛰면 안 된다고 느꼈다.",
        )
        save_btn = st.form_submit_button("✨ 작성 완료! 아래에 내 수업 활동지 만들기", type="primary", use_container_width=True)

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
        st.success("수업 활동지가 완성되었습니다! 아래에서 바로 인쇄하거나 파일로 저장해 보세요.")
        st.rerun()

    st.markdown("---")

    # 2) 완성된 수업 활동지 미리보기 & 원클릭 인쇄 / 저장
    st.subheader("2️⃣ 완성된 나의 수업 활동지 (인쇄 및 파일 저장)")
    st.caption("※ 창을 닫거나 새로고침하면 작성한 내용이 지워질 수 있으니, 지금 바로 아래 버튼으로 인쇄하거나 파일로 저장해 두세요!")

    sheet_html = _build_printable_activity_sheet_html(
        st.session_state.get("hq_student_label", ""),
        st.session_state.get("hq_group_label", ""),
    )

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.download_button(
            label="📥 선생님께 제출할 수업 활동지 파일 저장하기 (.html)",
            data=sheet_html,
            file_name="나의_보건미션_수업활동지.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )
    with btn_col2:
        # 활동지 텍스트 파일도 쉬운 이름으로 제공
        simple_txt = (
            f"[{SITE_CONFIG['site_title']} - 수업 활동지]\n"
            f"이름/학번: {st.session_state.get('hq_student_label', '미입력')} | 모둠: {st.session_state.get('hq_group_label', '미입력')}\n"
            f"실습 상황: {scenario['title']}\n\n"
            f"1) 친구와 생각 비교: {st.session_state['hq_team_notes'].get('peer_comparison', '-')}\n"
            f"2) 우리 모둠 최종 결론과 이유: {st.session_state['hq_team_notes'].get('team_conclusion', '-')}\n"
            f"3) 오늘 새로 깨달은 점: {st.session_state['hq_team_notes'].get('thought_change', '-')}\n"
        )
        st.download_button(
            label="📝 메모장으로 열리는 간단 활동지 저장하기 (.txt)",
            data=simple_txt,
            file_name="나의_보건미션_수업활동지.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # 화면 안에서 활동지 표를 그대로 보여주고 [🖨️ 지금 바로 인쇄 / PDF로 저장하기] 버튼이 작동하는 내장 뷰어
    components.html(sheet_html, height=620, scrolling=True)
