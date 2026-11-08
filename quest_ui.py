"""HEALTH QUEST — 예비 보건의료인의 미션룸: 교육용 UI·UX 렌더링 모듈."""
import json
import streamlit as st
from quest_data import SITE_CONFIG, UNIT_CATALOG
from quest_engine import (
    BADGE_DEFINITIONS,
    award_action_once,
    build_quest_export_payload,
    evaluate_mission_submission,
    generate_unit_inquiry_feedback,
    get_current_scenario_data,
    get_current_unit_data,
    get_scenario_progress,
    save_mission_reflection,
)


def inject_quest_css(reduce_motion: bool = False):
    """아이보리 배경(#FAF8F5), 딥 네이비 본문(#1B2A4A), 청록색 주요 버튼(#0D9488), 코랄 제한 강조(#E05A47) 테마 및 반응형 CSS."""
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
        /* 전체 배경 및 타이포그래피: 밝은 아이보리 배경 + 딥 네이비 본문 (OS 다크모드에서도 강제 라이트 톤 고정) */
        :root {{
            color-scheme: light !important;
        }}
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: #FAF8F5 !important;
            color: #1B2A4A !important;
            overflow-x: hidden !important;
        }}
        /* 상단 검정 헤더 바 제거 및 밝은 아이보리 통일 */
        header[data-testid="stHeader"] {{
            background-color: #FAF8F5 !important;
            color: #1B2A4A !important;
            border-bottom: 1px solid #E5E0D5;
        }}
        .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown {{
            color: #1B2A4A !important;
            line-height: 1.6;
            word-break: keep-all;
            overflow-wrap: break-word;
        }}
        h1, h2, h3, h4 {{
            color: #14223D !important;
            letter-spacing: -0.02em;
        }}
        /* 모든 입력창(Selectbox, Textarea, TextInput, Form, Expander) 검정 배경 원천 차단 → 흰색 배경 + 딥 네이비 글씨 */
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
        }}
        textarea::placeholder,
        input::placeholder {{
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
            opacity: 1 !important;
        }}
        /* 드롭다운 메뉴 팝오버 리스트도 밝은 흰색 배경으로 고정 */
        ul[data-baseweb="menu"],
        div[data-baseweb="popover"] div,
        li[role="option"] {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
        }}
        li[role="option"]:hover {{
            background-color: #F0FDFA !important;
        }}
        /* Form 및 Expander 카드 배경 밝게 고정 */
        [data-testid="stForm"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #E5E0D5 !important;
            border-radius: 14px !important;
            padding: 1.2rem !important;
        }}
        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
            border-color: #E5E0D5 !important;
            border-radius: 10px !important;
        }}
        /* 라디오 버튼 동그라미 테두리 및 선택 색상 선명화 */
        div[role="radiogroup"] label > div:first-child {{
            background-color: #FFFFFF !important;
            border: 2px solid #0D9488 !important;
        }}
        /* 사이드바 톤 조화 */
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
        /* 주요 행동 버튼: 청록색(#0D9488) 배경 + 흰색 텍스트 (명도 대비 확보) */
        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"] {{
            background-color: #0D9488 !important;
            color: #FFFFFF !important;
            border: 1px solid #0F766E !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            padding: 0.55rem 1.1rem !important;
            transition: transform 0.16s ease, background-color 0.16s ease, box-shadow 0.16s ease;
        }}
        div.stButton > button[kind="primary"] *,
        div.stFormSubmitButton > button[kind="primary"] * {{
            color: #FFFFFF !important;
        }}
        div.stButton > button[kind="primary"]:hover,
        div.stFormSubmitButton > button[kind="primary"]:hover {{
            background-color: #0F766E !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(13, 148, 136, 0.22);
        }}
        /* 보조 버튼 */
        div.stButton > button[kind="secondary"] {{
            background-color: #FFFFFF !important;
            color: #1B2A4A !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
            transition: background-color 0.15s ease, border-color 0.15s ease;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            background-color: #F0FDFA !important;
            border-color: #0D9488 !important;
        }}
        /* 카드형 레이아웃 */
        .hq-card {{
            background: #FFFFFF;
            border: 1px solid #E5E0D5;
            border-radius: 14px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 6px rgba(27, 42, 74, 0.04);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }}
        .hq-card-selected {{
            background: #F0FDFA;
            border: 2px solid #0D9488;
            border-radius: 14px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 14px rgba(13, 148, 136, 0.12);
        }}
        .hq-card-coral {{
            background: #FFFDFB;
            border-left: 4px solid #E05A47;
            border-top: 1px solid #F3DCD8;
            border-right: 1px solid #F3DCD8;
            border-bottom: 1px solid #F3DCD8;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 1rem;
        }}
        .hq-badge-teal {{
            display: inline-block;
            background: #CCFBF1;
            color: #0F766E !important;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            margin-right: 0.4rem;
        }}
        .hq-badge-coral {{
            display: inline-block;
            background: #FEE2E2;
            color: #B91C1C !important;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            margin-right: 0.4rem;
        }}
        .hq-badge-navy {{
            display: inline-block;
            background: #E2E8F0;
            color: #1B2A4A !important;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            margin-right: 0.4rem;
        }}
        /* 학습 흐름 7단계 안내 바 */
        .hq-step-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            background: #FFFFFF;
            border: 1px solid #E5E0D5;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
        }}
        .hq-step-pill {{
            font-size: 0.82rem;
            padding: 0.28rem 0.65rem;
            border-radius: 8px;
            background: #F1F5F9;
            color: #475569;
            font-weight: 500;
        }}
        .hq-step-pill.active {{
            background: #0D9488;
            color: #FFFFFF !important;
            font-weight: 600;
        }}
        /* 배지 획득 1회 효과 */
        @keyframes hqPopIn {{
            0% {{ opacity: 0; transform: translateY(-6px) scale(0.98); }}
            100% {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        .hq-award-banner {{
            background: linear-gradient(90deg, #F0FDFA 0%, #FFFDF9 100%);
            border: 1.5px solid #0D9488;
            border-radius: 12px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 1rem;
            animation: hqPopIn 0.28s ease-out 1;
        }}
        /* 모바일 및 태블릿 반응형 */
        @media (max-width: 768px) {{
            .hq-card, .hq-card-selected {{
                padding: 1rem;
            }}
            .hq-step-bar {{
                gap: 0.25rem;
                padding: 0.55rem;
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


def render_orientation_box(now_task: str, why_needed: str, next_step: str):
    """학생이 '지금 할 일', '이 활동이 필요한 이유', '다음 단계'를 즉시 이해하도록 안내."""
    st.markdown(
        f"""
        <div class="hq-card" style="background:#F8FAFC; border-left: 4px solid #0D9488; padding: 0.95rem 1.2rem;">
            <div style="font-size:0.92rem; margin-bottom:0.3rem;">
                <span class="hq-badge-teal">지금 할 일</span> <b>{now_task}</b>
            </div>
            <div style="font-size:0.88rem; color:#334155; margin-bottom:0.25rem;">
                • <b>이 활동이 필요한 이유</b>: {why_needed}
            </div>
            <div style="font-size:0.88rem; color:#334155;">
                • <b>다음 단계</b>: {next_step}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_one_time_notifications():
    """새 배지 획득 또는 전체 미션 완료 시 1회성 알림을 표시(애니메이션 대기 없이 즉시 다음 행동 가능)."""
    badge = st.session_state.pop("hq_pending_badge_notice", None)
    if badge:
        st.markdown(
            f"""
            <div class="hq-award-banner">
                <span class="hq-badge-teal">새 역량 배지 획득</span>
                <b>🏅 {badge['title']}</b> ({badge['competency']}) — {badge['desc']}
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
                <span class="hq-badge-coral">완전학습 달성 축하</span>
                <b>🎉 [{celeb}]의 3단계 임상 미션을 모두 완주했습니다!</b>
                이제 협력학습 탭에서 팀 공동 해결안을 정리하거나 학습 기록을 다운로드할 수 있습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_home_dashboard():
    """첫 화면: 오늘의 미션, 예상 소요시간, 학습목표, 진행률, 미션 시작/이어하기 주요 행동 버튼."""
    unit = get_current_unit_data()
    scenario = get_current_scenario_data()
    completed, total, ratio = get_scenario_progress(scenario)
    active_idx = st.session_state.get("hq_active_mission_idx", 0)
    current_mission = scenario["missions"][min(active_idx, len(scenario["missions"]) - 1)]

    render_orientation_box(
        now_task="오늘의 임상 미션과 학습목표를 확인하고 [미션 시작 / 이어하기] 버튼을 눌러 활동을 시작하세요.",
        why_needed="짧은 보건 현장 상황(3~5분)에서 단서를 찾고 판단 근거를 설명하는 훈련이 실제 병원 실습에서의 환자안전 역량을 길러줍니다.",
        next_step="단원 질문 & 가상 실습 상황 3개 중 1개 선택 → 3단계 미션 도전 및 피드백 → 팀 공동 해결안 작성",
    )

    col_main, col_stat = st.columns([1.65, 1], gap="medium")

    with col_main:
        st.markdown(
            f"""
            <div class="hq-card-selected">
                <div style="margin-bottom:0.5rem;">
                    <span class="hq-badge-teal">오늘의 미션</span>
                    <span class="hq-badge-navy">예상 소요시간: {current_mission['estimated_minutes']}~5분</span>
                    <span class="hq-badge-coral">{current_mission['question_type']}</span>
                </div>
                <h3 style="margin:0.2rem 0 0.5rem 0;">{scenario['title']}</h3>
                <p style="margin-bottom:0.6rem; font-weight:600; color:#0F766E;">
                    현재 도전 단계: {current_mission['title']}
                </p>
                <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:0.75rem 1rem; margin-bottom:0.6rem;">
                    <b>🎯 학습목표</b>: {current_mission['learning_objective']}
                </div>
                <div style="font-size:0.9rem; color:#334155;">
                    <b>PBL 실습 초점</b>: {scenario['pbl_focus']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        btn_label = "▶ 미션 이어하기 (진행 중)" if completed > 0 or st.session_state["hq_submissions"] else "▶ 오늘의 미션 시작하기 (3~5분)"
        c1, c2 = st.columns(2)
        with c1:
            if st.button(btn_label, type="primary", use_container_width=True, key="home_start_mission_btn"):
                st.session_state["hq_nav_view"] = "🩺 단계별 미션 수행"
                st.rerun()
        with c2:
            if st.button("🔍 단원 질문 & 가상 실습 상황 3개 고르기", type="secondary", use_container_width=True, key="home_explore_btn"):
                st.session_state["hq_nav_view"] = "🧭 단원 질문 & 실습상황 선택"
                st.rerun()

    with col_stat:
        earned_badges = st.session_state.get("hq_earned_badges", [])
        xp = st.session_state.get("hq_xp", 0)
        st.markdown(
            f"""
            <div class="hq-card">
                <h4 style="margin-top:0;">📊 나의 성장 및 진행 현황</h4>
                <p style="font-size:0.9rem; margin-bottom:0.3rem;">
                    <b>선택 시나리오 진행률</b>: {completed} / {total} 미션 완료 ({int(ratio * 100)}%)
                </p>
                <p style="font-size:0.9rem; margin-bottom:0.3rem;">
                    <b>누적 학습 성취도</b>: {xp} pt <span style="font-size:0.8rem; color:#475569;">(근거 설명·개선 중심 보상)</span>
                </p>
                <p style="font-size:0.9rem; margin-bottom:0.4rem;">
                    <b>달성 역량 배지</b>: {len(earned_badges)} / {len(BADGE_DEFINITIONS)}개
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(ratio, text=f"현재 실습 상황 완료율: {int(ratio * 100)}%")

        # 팀 공동 목표 (개인 순위표 대신 공동 목표 제시)
        team_contrib = min(100, int(ratio * 60) + (20 if st.session_state["hq_unit_questions"] else 0) + (20 if st.session_state["hq_team_notes"].get("team_conclusion") else 0))
        st.markdown(
            f"""
            <div class="hq-card" style="padding:0.9rem 1.1rem;">
                <div style="font-size:0.85rem; font-weight:600; color:#0F766E; margin-bottom:0.25rem;">
                    🤝 {SITE_CONFIG['team_goal_title']}
                </div>
                <div style="font-size:0.83rem; color:#334155;">
                    개인 순위 경쟁 없이, 우리 모둠의 근거 비교와 안전 수칙 완수로 공동 목표를 채웁니다. (현재 모둠 기여 달성도: <b>{team_contrib}%</b>)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_unit_inquiry_and_scenario_selection():
    """단원 질문(개념·의학용어) → AI 보건튜터 단계별 피드백 → 가상 실습 상황 3개 중 1개 선택."""
    unit = get_current_unit_data()
    current_scen = get_current_scenario_data()

    render_orientation_box(
        now_task="단원에서 궁금한 의학용어나 개념을 질문하고, 제시된 가상 실습 상황 3개(A·B·C) 중 최종 1개를 선택하세요.",
        why_needed="내가 궁금한 개념을 실제 병동 상황과 연결해 직접 실습 시나리오를 고를 때 자기주도학습능력과 임상 추론력이 높아집니다.",
        next_step="가상 실습 상황 1개 선택 완료 후 [이 실습 상황으로 3단계 미션 도전하기] 클릭",
    )

    st.markdown(
        """
        <div class="hq-card-coral">
            <b>🔒 개인정보 및 건강정보 보호 안내</b>: 본 학습 공간에는 실제 환자의 실명·병원명이나 학생 본인의 실제 질환·건강정보를 입력하지 마세요. 모든 실습은 가상의 환자 사례로만 진행됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_q, col_terms = st.columns([1.4, 1], gap="medium")

    with col_q:
        st.subheader("1️⃣ 단원 개념·의학용어 질문하기 (AI 보건튜터 코칭)")
        with st.form("unit_inquiry_form", clear_on_submit=False):
            student_level = st.selectbox(
                "나의 사전 이해도 선택",
                [
                    "기초 (용어 뜻과 쉬운 비유부터 차근차근 알고 싶어요)",
                    "중급 (개념은 알지만 실제 병동 상황에서 어떻게 적용하는지 궁금해요)",
                    "심화 (우선순위 판단 근거와 예외 상황까지 깊게 탐구하고 싶어요)",
                ],
                index=0,
            )
            q_input = st.text_input(
                "궁금한 의학용어, 개념, 또는 실습 질문을 적어 주세요",
                placeholder="예: 비말주의와 접촉주의는 언제 구분해 쓰나요? / 빈뇨와 다뇨는 어떻게 다른가요?",
            )
            submitted_q = st.form_submit_button("💬 AI 보건튜터에게 질문하고 실습 상황 연결받기", type="primary", use_container_width=True)

        if submitted_q:
            if not q_input.strip():
                st.warning("궁금한 용어나 개념 질문을 한 문장으로 입력해 주세요.")
            else:
                generate_unit_inquiry_feedback(unit, q_input, student_level.split("(")[0].strip())
                st.rerun()

        if st.session_state["hq_unit_questions"]:
            latest_q = st.session_state["hq_unit_questions"][-1]
            st.markdown(
                f"""
                <div class="hq-card" style="background:#F0FDFA; border-color:#0D9488;">
                    <span class="hq-badge-teal">AI 보건튜터 단계별 피드백</span>
                    <span class="hq-badge-navy">질문: {latest_q['question']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(latest_q["feedback_markdown"])

    with col_terms:
        st.subheader("📘 단원 핵심 의학용어 사전")
        st.caption(f"현재 단원: {st.session_state['hq_selected_unit']}")
        for term, desc in unit["key_terms"].items():
            st.markdown(
                f"""
                <div class="hq-card" style="padding:0.85rem 1rem; margin-bottom:0.6rem;">
                    <div style="font-weight:700; color:#0F766E; margin-bottom:0.2rem;">• {term}</div>
                    <div style="font-size:0.88rem; color:#334155;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("2️⃣ 가상 실습 상황 3개 중 최종 1개 선택하기")
    st.caption("각 카드의 실습 초점과 난이도를 비교한 뒤, 오늘 도전할 최종 실습 상황 1개를 선택하세요.")

    scen_cols = st.columns(3, gap="medium")
    for idx, scen in enumerate(unit["scenarios"]):
        is_selected = scen["scenario_id"] == current_scen["scenario_id"]
        c_done, c_total, _ = get_scenario_progress(scen)
        card_class = "hq-card-selected" if is_selected else "hq-card"
        status_tag = "✅ 현재 선택됨" if is_selected else "선택 가능"

        with scen_cols[idx]:
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div style="margin-bottom:0.4rem;">
                        <span class="hq-badge-teal">가상 실습 {scen['code']}</span>
                        <span class="hq-badge-navy">{scen['difficulty']}</span>
                    </div>
                    <h4 style="margin:0.2rem 0 0.5rem 0; font-size:1.03rem;">{scen['title']}</h4>
                    <p style="font-size:0.88rem; color:#334155; margin-bottom:0.6rem;">{scen['summary']}</p>
                    <div style="font-size:0.82rem; color:#0F766E; background:#FFFFFF; padding:0.5rem 0.65rem; border-radius:8px; border:1px solid #E2E8F0; margin-bottom:0.5rem;">
                        <b>PBL 흐름</b>: {scen['pbl_focus']}
                    </div>
                    <div style="font-size:0.8rem; color:#475569;">
                        진행 현황: {c_done}/{c_total} 미션 완료 · <b>{status_tag}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            btn_type = "primary" if is_selected else "secondary"
            btn_text = f"✔ 상황 {scen['code']} 선택됨 (미션 시작)" if is_selected else f"상황 {scen['code']} 최종 선택하기"
            if st.button(btn_text, key=f"select_scen_{scen['scenario_id']}", type=btn_type, use_container_width=True):
                st.session_state["hq_selected_scenario_id"] = scen["scenario_id"]
                st.session_state["hq_active_mission_idx"] = 0
                st.session_state["hq_nav_view"] = "🩺 단계별 미션 수행"
                st.rerun()


def render_mission_runner():
    """7단계 학습 흐름: 상황 확인 → 핵심 정보 탐색 → 판단 선택 → 근거 작성 → 피드백 → 재도전 → 성찰."""
    scenario = get_current_scenario_data()
    missions = scenario["missions"]
    active_idx = min(st.session_state.get("hq_active_mission_idx", 0), len(missions) - 1)
    mission = missions[active_idx]
    m_id = mission["id"]
    existing_sub = st.session_state["hq_submissions"].get(m_id)
    existing_ref = st.session_state["hq_reflections"].get(m_id, "")

    # 현재 7단계 중 활성 단계 계산
    if not existing_sub:
        current_flow_step = 3  # 상황확인(1)·정보탐색(2)·판단선택(3)·근거작성(4) 진행 중
    elif not existing_sub["is_correct"]:
        current_flow_step = 6  # 피드백(5) 및 재도전(6) 단계
    elif not existing_ref:
        current_flow_step = 7  # 성찰(7) 단계
    else:
        current_flow_step = 7

    flow_labels = [
        (1, "1. 상황 확인"),
        (2, "2. 핵심 정보 탐색"),
        (3, "3. 판단 선택"),
        (4, "4. 근거 작성"),
        (5, "5. 피드백"),
        (6, "6. 재도전·보완"),
        (7, "7. 성찰"),
    ]
    pills_html = "".join(
        [
            f'<span class="hq-step-pill {"active" if step_no <= current_flow_step else ""}">{label}</span>'
            for step_no, label in flow_labels
        ]
    )
    st.markdown(f'<div class="hq-step-bar">{pills_html}</div>', unsafe_allow_html=True)

    render_orientation_box(
        now_task=f"[{mission['title']}]의 임상 단서를 읽고 가장 적절한 판단 선택지와 그 이유(근거)를 작성해 제출하세요.",
        why_needed=mission["learning_objective"],
        next_step="제출 후 선택지별 해설·피드백 확인 → 놓친 단서 보완 재도전 → 성찰 질문 기록 후 다음 미션 이동",
    )

    # 상단 미션 1 / 2 / 3 전환 버튼
    m_cols = st.columns(len(missions))
    for i, m_item in enumerate(missions):
        sub_i = st.session_state["hq_submissions"].get(m_item["id"])
        done_mark = "✅ " if (sub_i and sub_i.get("is_correct") and len(sub_i.get("rationale", "")) >= 5) else ""
        b_type = "primary" if i == active_idx else "secondary"
        with m_cols[i]:
            if st.button(
                f"{done_mark}미션 {m_item['step_num']} ({m_item['question_type'].split(' ')[0]})",
                key=f"tab_btn_{m_item['id']}",
                type=b_type,
                use_container_width=True,
            ):
                st.session_state["hq_active_mission_idx"] = i
                st.rerun()

    # [1단계: 상황 확인] & [2단계: 핵심 정보 탐색]
    col_sit, col_clue = st.columns([1.35, 1], gap="medium")
    with col_sit:
        st.markdown(
            f"""
            <div class="hq-card">
                <div style="margin-bottom:0.45rem;">
                    <span class="hq-badge-teal">미션 {mission['step_num']} / {len(missions)}</span>
                    <span class="hq-badge-coral">{mission['question_type']}</span>
                    <span class="hq-badge-navy">⏱ 소요시간 {mission['estimated_minutes']}분</span>
                </div>
                <h3 style="margin:0.2rem 0 0.6rem 0;">{mission['title']}</h3>
                <p style="font-size:0.96rem; background:#FAF8F5; padding:0.9rem 1rem; border-radius:10px; border:1px solid #E5E0D5;">
                    <b>📋 현장 상황</b>: {mission['situation']}
                </p>
                <div style="font-size:0.84rem; color:#475569; margin-top:0.5rem;">
                    📚 <b>참고 출처</b>: {mission['reference_source']} · <b>검토 상태</b>: {mission['teacher_review_status']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_clue:
        clues_li = "".join([f"<li style='margin-bottom:0.35rem;'>{c}</li>" for c in mission["clinical_clues"]])
        st.markdown(
            f"""
            <div class="hq-card" style="background:#F0FDFA; border-color:#99F6E4;">
                <h4 style="margin-top:0; color:#0F766E;">🔎 핵심 임상 단서 탐색</h4>
                <ul style="padding-left:1.2rem; margin-bottom:0.5rem; font-size:0.9rem;">
                    {clues_li}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("💡 판단이 어려울 때 핵심 힌트 보기 (정답 미노출)"):
            st.info(mission["hint"])

    # [3단계: 판단 선택] & [4단계: 근거 작성] (제출 전에는 정답·해설 절대 비공개)
    st.markdown(f"#### ✍️ 판단 선택 및 근거 작성 — {mission['question']}")
    st.caption("실제 환자 정보나 개인 건강정보는 적지 마시고, 교과서 원리와 환자 안전 관점에서 판단 이유를 작성해 주세요.")

    default_idx = existing_sub["selected_idx"] if existing_sub else 0
    default_rationale = existing_sub["rationale"] if existing_sub else ""

    with st.form(key=f"mission_form_{m_id}", clear_on_submit=False):
        selected_option = st.radio(
            "가장 적절한 간호 판단 선택지 (1개 선택)",
            options=list(range(len(mission["options"]))),
            format_func=lambda idx: f"{idx + 1}번. {mission['options'][idx]}",
            index=default_idx,
            key=f"radio_{m_id}",
        )
        rationale_input = st.text_area(
            "그렇게 판단한 임상적 근거를 1~2문장으로 설명해 주세요 (서술형 근거 평가 반영)",
            value=default_rationale,
            placeholder="예: 분비물 노출 가능성이 있고 장갑이 손 위생을 대체할 수 없으므로 흐르는 물과 비누로 40~60초간 씻어야 교차감염을 막을 수 있습니다.",
            height=95,
            key=f"rationale_{m_id}",
        )
        submit_label = "🔄 피드백을 반영하여 다시 제출하기 (재도전)" if existing_sub else "✅ 판단 및 근거 제출하기"
        submitted = st.form_submit_button(submit_label, type="primary", use_container_width=True)

    if submitted:
        evaluate_mission_submission(mission, selected_option, rationale_input)
        st.rerun()

    # [5단계: 피드백] & [6단계: 재도전] (제출 완료 후에만 공개!)
    sub = st.session_state["hq_submissions"].get(m_id)
    if sub:
        st.markdown("---")
        st.subheader("📬 AI 보건튜터 피드백 및 선택지별 해설")

        col_fb1, col_fb2 = st.columns(2, gap="medium")
        with col_fb1:
            if sub["is_correct"]:
                st.markdown(
                    f"""
                    <div class="hq-card-selected">
                        <span class="hq-badge-teal">객관식 판단 평가: 정답 확인</span>
                        <span class="hq-badge-navy">시도 횟수: {sub['attempts']}회</span>
                        <h4 style="margin:0.4rem 0; color:#0F766E;">✅ 정확한 임상 판단입니다!</h4>
                        <p style="font-size:0.9rem; margin-bottom:0;">
                            선택하신 <b>{sub['selected_idx'] + 1}번</b> 행동이 환자 안전과 감염관리 표준지침에 정확히 부합합니다.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # 오답 시 비난이나 감점 없이 놓친 단서와 다시 생각할 질문 제시
                st.markdown(
                    f"""
                    <div class="hq-card-coral">
                        <span class="hq-badge-coral">다시 생각해 보기 (감점 없음)</span>
                        <span class="hq-badge-navy">시도 횟수: {sub['attempts']}회</span>
                        <h4 style="margin:0.4rem 0;">🧭 놓친 단서를 함께 다시 확인해 볼까요?</h4>
                        <p style="font-size:0.9rem; margin-bottom:0.4rem;">
                            <b>선택하신 항목 해설</b>: {mission['option_explanations'][sub['selected_idx']]}
                        </p>
                        <p style="font-size:0.9rem; background:#FFFFFF; padding:0.65rem 0.85rem; border-radius:8px; margin-bottom:0;">
                            💡 <b>{mission['missed_clue_guide']}</b><br>
                            위 입력창에서 선택지와 근거를 수정한 뒤 <b>[🔄 피드백을 반영하여 다시 제출하기]</b> 버튼을 눌러 재도전해 보세요!
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_fb2:
            st.markdown(
                f"""
                <div class="hq-card">
                    <span class="hq-badge-navy">서술형 근거 평가 (객관식과 분리 평가)</span>
                    <h4 style="margin:0.4rem 0;">📝 나의 판단 근거 검토</h4>
                    <p style="font-size:0.88rem; color:#334155; background:#F8FAFC; padding:0.6rem 0.8rem; border-radius:8px;">
                        "{sub['rationale'] if sub['rationale'] else '(아직 근거를 입력하지 않았습니다)'}"
                    </p>
                    <p style="font-size:0.88rem; margin-bottom:0;">
                        <b>코칭 피드백</b>: {sub['rationale_status']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 선택지별 전체 해설 (제출 이후 공개)
        with st.expander("📖 선택지 1~4번 전체 상세 해설 및 출처 확인하기", expanded=sub["is_correct"]):
            for idx, exp_text in enumerate(mission["option_explanations"]):
                prefix = "✅ [정답] " if idx == mission["correct_index"] else f"• [{idx + 1}번 보기] "
                st.markdown(f"**{prefix}{mission['options'][idx]}**\n  - 해설: {exp_text}")
            st.caption(f"근거 출처: {mission['reference_source']} ({mission['teacher_review_status']})")

        # [7단계: 성찰] 및 다음 미션 이동
        st.markdown("#### 🌱 7단계 · 성찰 기록 및 다음 단계 이동")
        with st.form(key=f"reflection_form_{m_id}", clear_on_submit=False):
            ref_val = st.text_input(
                f"💭 성찰 질문: {mission['reflection_prompt']}",
                value=existing_ref,
                placeholder="오늘 미션에서 깨달은 나만의 현장 적용 다짐을 한 문장으로 적어 보세요.",
            )
            ref_saved = st.form_submit_button("💾 성찰 기록 저장하기 (+20 pt)", type="secondary")
        if ref_saved:
            if save_mission_reflection(mission, ref_val):
                st.success("성찰 기록이 나의 성장 로그에 저장되었습니다!")
                st.rerun()
            else:
                st.warning("성찰 내용을 한 문장으로 입력해 주세요.")

        nav_c1, nav_c2 = st.columns(2)
        with nav_c1:
            if active_idx < len(missions) - 1:
                if st.button(f"▶ 다음 미션(미션 {active_idx + 2})으로 이동하기", type="primary", use_container_width=True):
                    st.session_state["hq_active_mission_idx"] = active_idx + 1
                    st.rerun()
            else:
                if st.button("🤝 3단계 미션 완료! 팀 협력학습(공동 해결안)으로 이동", type="primary", use_container_width=True):
                    st.session_state["hq_nav_view"] = "🤝 팀 협력학습 & 성장 기록"
                    st.rerun()
        with nav_c2:
            if st.button("🏠 미션룸 홈 화면으로", type="secondary", use_container_width=True):
                st.session_state["hq_nav_view"] = "🏠 미션룸 홈"
                st.rerun()


def render_collaboration_and_growth():
    """협력학습(개인 판단 → 팀원 근거 비교 → 팀 공동 해결안 작성) 및 성장 기록·다운로드."""
    scenario = get_current_scenario_data()

    render_orientation_box(
        now_task="개인 미션에서 작성한 나의 근거를 팀원과 비교하고, 우리 모둠의 공동 해결안과 토의 후 바뀐 생각을 기록하세요.",
        why_needed="병원 현장은 다학제·팀 협력이 필수입니다. 서로 놓친 임상 단서를 비교하며 더 안전한 간호 의사결정에 도달할 수 있습니다.",
        next_step="팀 공동 해결안 저장 후 [학습 결과 JSON / TXT 다운로드]로 과제 제출용 파일 보관",
    )

    st.markdown(
        """
        <div class="hq-card-coral">
            <b>ℹ️ 협력학습 시연 모드(한 기기 함께 작성) 및 데이터 보존 범위 안내</b><br>
            현재 외부 실시간 데이터베이스(영속 저장소)가 연결되어 있지 않으므로, 다른 학생의 세션과 데이터가 섞이지 않도록 <b>현재 브라우저 세션(`st.session_state`) 내에서 한 기기로 모둠원이 함께 작성하는 시연 모드</b>로 작동합니다. 새로고침이나 브라우저 종료 시 세션 기록이 초기화될 수 있으니 작성 후 반드시 아래 <b>결과 다운로드 버튼</b>으로 파일을 저장하세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.25, 1], gap="medium")

    with col_left:
        st.subheader("🤝 PBL 3단계 협력학습 워크스페이스")
        st.caption(f"대상 실습 상황: {scenario['title']}")

        # 내가 작성한 미션별 근거 요약 자동 불러오기
        my_rationales = []
        for m in scenario["missions"]:
            sub = st.session_state["hq_submissions"].get(m["id"])
            if sub and sub.get("rationale"):
                my_rationales.append(f"- [미션 {m['step_num']}] {sub['rationale']}")
        auto_my_summary = "\n".join(my_rationales) if my_rationales else ""

        notes = st.session_state.get("hq_team_notes", {})
        with st.form("team_collab_form", clear_on_submit=False):
            my_sum = st.text_area(
                "1단계 · 나의 개인 판단 및 근거 요약",
                value=notes.get("my_summary") or auto_my_summary,
                placeholder="미션 1~3에서 내가 세운 핵심 판단 근거가 자동으로 채워지거나 직접 요약할 수 있습니다.",
                height=85,
            )
            peer_comp = st.text_area(
                "2단계 · 팀원과 근거 비교 (나와 같았던 점 / 팀원이 새롭게 제시한 임상 단서)",
                value=notes.get("peer_comparison", ""),
                placeholder="예: 나는 손 위생 시간(40~60초)만 생각했는데, 팀원은 주변 환자와의 거리(1~2m 확보) 단서를 추가로 짚어주었다.",
                height=85,
            )
            team_conc = st.text_area(
                "3단계 · 우리 팀의 공동 해결안 (최종 간호 우선순위 결론)",
                value=notes.get("team_conclusion", ""),
                placeholder="예: 1순위 의료진·환자 마스크 착용 및 거리 분리 → 2순위 활력징후 사정 → 3순위 규정 소독제 사용 및 손상성 폐기물 즉시 폐기",
                height=85,
            )
            team_rat = st.text_area(
                "4단계 · 팀 공동 해결안의 핵심 근거",
                value=notes.get("team_rationale", ""),
                placeholder="표준주의와 비말주의 지침에 따라 감염원의 탈출과 침입 경로를 동시에 차단하기 위함이다.",
                height=75,
            )
            thought_chg = st.text_area(
                "5단계 · 팀 토의 후 바뀐 나의 생각 (성장 성찰)",
                value=notes.get("thought_change", ""),
                placeholder="예: 처치 속도보다 환자와 의료진 모두의 안전 보호구·폐기물 원칙이 먼저라는 점을 명확히 깨달았다.",
                height=75,
            )
            save_team = st.form_submit_button("💾 팀 공동 해결안 저장 및 협업 역량 기록하기", type="primary", use_container_width=True)

        if save_team:
            if not team_conc.strip() or not team_rat.strip():
                st.warning("팀 공동 해결안(결론)과 핵심 근거를 입력해 주세요.")
            else:
                st.session_state["hq_team_notes"] = {
                    "my_summary": my_sum.strip(),
                    "peer_comparison": peer_comp.strip(),
                    "team_conclusion": team_conc.strip(),
                    "team_rationale": team_rat.strip(),
                    "thought_change": thought_chg.strip(),
                    "saved_at": "방금 저장됨",
                }
                award_action_once(
                    action_key=f"team_collab:{scenario['scenario_id']}",
                    action_type="협력학습 완료",
                    label=f"[{scenario['title']}] 팀 근거 비교 및 공동 해결안 작성 완료",
                    xp_gain=40,
                    badge_id="team_collaborator",
                )
                st.success("팀 공동 해결안이 저장되었으며 '협력적 문제해결 팀원' 역량이 기록되었습니다!")
                st.rerun()

    with col_right:
        st.subheader("🏅 나의 성장 기록 및 역량 배지")
        earned = st.session_state.get("hq_earned_badges", [])
        for b_id, b_info in BADGE_DEFINITIONS.items():
            is_unlocked = b_id in earned
            badge_style = "hq-card-selected" if is_unlocked else "hq-card"
            icon_txt = "🏅 획득 완료" if is_unlocked else "🔒 미획득"
            st.markdown(
                f"""
                <div class="{badge_style}" style="padding:0.75rem 1rem; margin-bottom:0.55rem;">
                    <div style="font-size:0.8rem; font-weight:600; color:#0F766E;">{icon_txt} · {b_info['competency']}</div>
                    <div style="font-weight:700; font-size:0.95rem;">{b_info['title']}</div>
                    <div style="font-size:0.83rem; color:#475569;">{b_info['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("#### 📜 행동 기반 성장 로그 (중복 지급 방지 적용)")
        logs = st.session_state.get("hq_growth_log", [])
        if logs:
            for item in reversed(logs[-8:]):
                st.markdown(f"- `{item['timestamp']}` **[{item['type']}]** {item['label']} *(+{item['xp']} pt)*")
        else:
            st.caption("아직 기록된 학습 행동이 없습니다. 미션 제출이나 근거 작성을 시작해 보세요!")

        st.markdown("---")
        st.markdown("#### 📥 학습 결과 파일 다운로드 (영구 보관용)")
        export_data = build_quest_export_payload()
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        txt_lines = [
            f"[{export_data['site_title']}] 학습 및 협력학습 결과 보고서",
            f"- 단원: {export_data['selected_unit']}",
            f"- 선택 실습 상황: {export_data['selected_scenario']}",
            f"- 미션 진행률: {export_data['progress']} / 성취 점수: {export_data['xp']} pt",
            f"- 획득 배지: {', '.join(export_data['earned_badges']) if export_data['earned_badges'] else '없음'}",
            "",
            "[미션별 제출 근거 및 평가]",
        ]
        for mid, sdata in export_data["mission_submissions"].items():
            txt_lines.append(
                f"- {mid}: 선택={sdata['selected_idx']+1}번 ({'정답' if sdata['is_correct'] else '재도전 필요'}) | 근거={sdata['rationale']} | 상태={sdata['teacher_review_status']}"
            )
        txt_lines.append("\n[팀 공동 해결안]")
        tn = export_data["team_collaboration"]
        txt_lines.append(f"- 팀 결론: {tn.get('team_conclusion', '')}")
        txt_lines.append(f"- 팀 근거: {tn.get('team_rationale', '')}")
        txt_lines.append(f"- 토의 후 바뀐 생각: {tn.get('thought_change', '')}")

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                "📥 전체 결과 저장 (JSON)",
                data=json_str,
                file_name="health_quest_learning_record.json",
                mime="application/json",
                use_container_width=True,
            )
        with d_col2:
            st.download_button(
                "📄 제출용 요약본 (TXT)",
                data="\n".join(txt_lines),
                file_name="health_quest_learning_record.txt",
                mime="text/plain",
                use_container_width=True,
            )

