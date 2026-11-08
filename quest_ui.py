"""HEALTH QUEST — 사설 스마트 디지털 학습지 스타일 UI·UX 모듈 (다채로운 파스텔·그라데이션 컬러, 입체 3D 인터랙티브 버튼, Web Audio 효과음, 교사용 제출물 관리함 포함)."""
import html
import streamlit as st
import streamlit.components.v1 as components
from quest_data import SITE_CONFIG
from quest_engine import (
    BADGE_DEFINITIONS,
    evaluate_mission_submission,
    export_submitted_reports_csv,
    generate_or_save_teacher_feedback,
    get_current_scenario_data,
    get_current_unit_data,
    get_scenario_progress,
    get_step_completion_flags,
    get_unit_questions_for_current,
    load_submitted_reports,
    save_mission_reflection,
    submit_final_report_to_teacher,
    submit_student_questions_and_get_feedback,
    submit_team_collaboration_and_get_feedback,
)


def _md_html(raw_html: str):
    """
    Markdown의 '4칸 들여쓰기 코드블록(<pre><code>) 변환 버그'를 원천 차단하는 헬퍼 함수.
    모든 줄의 앞뒤 공백을 제거하고 빈 줄을 없애서 </div>, <h1> 등의 태그가 절대 화면에 노출되지 않게 보장합니다.
    """
    cleaned = "\n".join(line.strip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def inject_quest_css(reduce_motion: bool = False):
    """사설 스마트 디지털 학습지(아이스크림·엘리하이·밀크T 감성) 컬러 팔레트 및 입체 인터랙션 CSS."""
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
        else ""
    )

    _md_html(
        f"""
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

        :root {{
            color-scheme: light !important;
        }}
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background: linear-gradient(165deg, #EEF2FF 0%, #F0FDF4 48%, #FFFBEB 100%) !important;
            background-attachment: fixed !important;
            color: #1E293B !important;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif !important;
            letter-spacing: -0.015em !important;
            word-spacing: 0.02em !important;
            overflow-x: hidden !important;
        }}
        .block-container {{
            max-width: 1140px !important;
            margin: 0 auto !important;
            padding-top: 1.35rem !important;
            padding-bottom: 3.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}
        header[data-testid="stHeader"] {{
            background: rgba(255, 255, 255, 0.88) !important;
            backdrop-filter: blur(8px);
            color: #1E293B !important;
            border-bottom: 1px solid #E0E7FF;
        }}
        .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown {{
            color: #1E293B !important;
            line-height: 1.7 !important;
            word-break: keep-all !important;
            overflow-wrap: break-word !important;
        }}
        h1, h2, h3, h4 {{
            color: #0F172A !important;
            font-family: 'Pretendard', sans-serif !important;
            letter-spacing: -0.025em !important;
            line-height: 1.36 !important;
            word-break: keep-all !important;
        }}

        /* 키프레임 애니메이션: 카드 팝업 등장 & 진도바 반짝임 */
        @keyframes hqPopIn {{
            0% {{ opacity: 0; transform: translateY(10px) scale(0.99); }}
            100% {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        @keyframes hqShimmer {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        @keyframes hqPulseBadge {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.04); }}
        }}

        /* 상단 히어로 배너 (사설 디지털 학습지 스타일 그라데이션) */
        .hq-hero-banner {{
            background: linear-gradient(135deg, #4F46E5 0%, #0EA5E9 52%, #10B981 100%);
            border-radius: 20px;
            padding: 1.35rem 1.75rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 25px rgba(79, 70, 229, 0.22);
            color: #FFFFFF !important;
            position: relative;
            overflow: hidden;
            animation: hqPopIn 0.35s ease-out;
        }}
        .hq-hero-banner h1 {{
            color: #FFFFFF !important;
            margin: 0.25rem 0 0 0 !important;
            font-size: 1.75rem !important;
            font-weight: 800 !important;
            text-shadow: 0 2px 6px rgba(15, 23, 42, 0.18);
        }}
        .hq-hero-sub {{
            color: #E0F2FE !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            margin-top: 0.2rem !important;
        }}
        .hq-hero-pill {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.22);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.4);
            color: #FFFFFF !important;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.22rem 0.75rem;
            border-radius: 999px;
            margin-right: 0.4rem;
            margin-bottom: 0.25rem;
        }}

        /* 입력창 화사한 테두리 및 포커스 글로우 */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"],
        div[data-baseweb="base-input"],
        textarea,
        input[type="text"] {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 2px solid #C7D2FE !important;
            border-radius: 12px !important;
            -webkit-text-fill-color: #0F172A !important;
            caret-color: #4F46E5 !important;
            font-size: 0.95rem !important;
            transition: all 0.18s ease !important;
        }}
        textarea:focus,
        input[type="text"]:focus {{
            border-color: #6366F1 !important;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.18) !important;
            transform: translateY(-1px);
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
            color: #0F172A !important;
        }}
        li[role="option"]:hover {{
            background-color: #EEF2FF !important;
        }}

        /* 폼 컨테이너 (사설 학습지 워크시트 프레임) */
        [data-testid="stForm"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            border: 2px solid #C7D2FE !important;
            border-top: 5px solid #6366F1 !important;
            border-radius: 18px !important;
            padding: 1.45rem 1.65rem !important;
            box-shadow: 0 8px 20px rgba(79, 70, 229, 0.07);
            animation: hqPopIn 0.3s ease-out;
        }}
        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary {{
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            border-color: #C7D2FE !important;
            border-radius: 12px !important;
        }}
        div[role="radiogroup"] label {{
            padding: 0.42rem 0.6rem !important;
            border-radius: 10px !important;
            transition: background-color 0.15s ease, transform 0.15s ease !important;
        }}
        div[role="radiogroup"] label:hover {{
            background-color: #EEF2FF !important;
            transform: translateX(4px);
        }}
        div[role="radiogroup"] label > div:first-child {{
            background-color: #FFFFFF !important;
            border: 2px solid #4F46E5 !important;
        }}

        /* 사이드바 화사한 파스텔 톤 */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F5F3FF 100%) !important;
            border-right: 2px solid #E0E7FF;
        }}
        section[data-testid="stSidebar"] * {{
            color: #1E293B !important;
        }}
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] input {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
        }}

        /* ==============================================================
           입체 3D 인터랙티브 버튼 (마우스 올릴 때 커지고 클릭할 때 쏙 눌리는 효과)
           ============================================================== */
        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"],
        div.stDownloadButton > button {{
            background: linear-gradient(135deg, #4F46E5 0%, #0EA5E9 55%, #10B981 100%) !important;
            background-size: 200% 200% !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            font-size: 0.97rem !important;
            padding: 0.72rem 1.25rem !important;
            box-shadow: 0 5px 0 #3730A3, 0 8px 16px rgba(79, 70, 229, 0.28) !important;
            transition: transform 0.16s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.16s ease, filter 0.16s ease !important;
            cursor: pointer !important;
        }}
        div.stButton > button[kind="primary"] *,
        div.stFormSubmitButton > button[kind="primary"] *,
        div.stDownloadButton > button * {{
            color: #FFFFFF !important;
        }}
        div.stButton > button[kind="primary"]:hover,
        div.stFormSubmitButton > button[kind="primary"]:hover,
        div.stDownloadButton > button:hover {{
            transform: translateY(-3px) scale(1.022) !important;
            box-shadow: 0 8px 0 #3730A3, 0 14px 24px rgba(14, 165, 233, 0.36) !important;
            filter: brightness(1.05);
        }}
        div.stButton > button[kind="primary"]:active,
        div.stFormSubmitButton > button[kind="primary"]:active,
        div.stDownloadButton > button:active {{
            transform: translateY(3px) scale(0.965) !important;
            box-shadow: 0 2px 0 #3730A3, 0 4px 8px rgba(79, 70, 229, 0.2) !important;
        }}

        /* 보조 버튼 (화이트·파스텔 3D 입체 버튼) */
        div.stButton > button[kind="secondary"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
            color: #312E81 !important;
            border: 2px solid #C7D2FE !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            font-size: 0.93rem !important;
            padding: 0.65rem 1.05rem !important;
            box-shadow: 0 4px 0 #CBD5E1, 0 4px 10px rgba(15, 23, 42, 0.05) !important;
            transition: transform 0.16s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.16s ease, background-color 0.16s ease, border-color 0.16s ease !important;
            cursor: pointer !important;
        }}
        div.stButton > button[kind="secondary"] * {{
            color: #312E81 !important;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            background: linear-gradient(180deg, #EEF2FF 0%, #E0E7FF 100%) !important;
            border-color: #6366F1 !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 0 #A5B4FC, 0 10px 18px rgba(99, 102, 241, 0.18) !important;
        }}
        div.stButton > button[kind="secondary"]:active {{
            transform: translateY(3px) scale(0.965) !important;
            box-shadow: 0 1px 0 #A5B4FC, 0 2px 4px rgba(99, 102, 241, 0.12) !important;
        }}

        /* 스마트 디지털 학습지 컬러풀 카드 시스템 */
        .hq-card {{
            background: #FFFFFF;
            border: 2px solid #E0E7FF;
            border-radius: 18px;
            padding: 1.35rem 1.55rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.06);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: hqPopIn 0.32s ease-out;
        }}
        .hq-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 24px rgba(79, 70, 229, 0.12);
        }}
        .hq-card-level-0 {{
            background: linear-gradient(180deg, #FFFFFF 0%, #ECFDF5 100%);
            border: 2px solid #6EE7B7;
            border-top: 6px solid #10B981;
            border-radius: 18px;
            padding: 1.35rem 1.55rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: hqPopIn 0.32s ease-out;
        }}
        .hq-card-level-0:hover {{ transform: translateY(-4px) scale(1.01); }}
        .hq-card-level-1 {{
            background: linear-gradient(180deg, #FFFFFF 0%, #EFF6FF 100%);
            border: 2px solid #93C5FD;
            border-top: 6px solid #3B82F6;
            border-radius: 18px;
            padding: 1.35rem 1.55rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: hqPopIn 0.35s ease-out;
        }}
        .hq-card-level-1:hover {{ transform: translateY(-4px) scale(1.01); }}
        .hq-card-level-2 {{
            background: linear-gradient(180deg, #FFFFFF 0%, #FFF7ED 100%);
            border: 2px solid #FDBA74;
            border-top: 6px solid #F97316;
            border-radius: 18px;
            padding: 1.35rem 1.55rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 16px rgba(249, 115, 22, 0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: hqPopIn 0.38s ease-out;
        }}
        .hq-card-level-2:hover {{ transform: translateY(-4px) scale(1.01); }}

        .hq-card-selected {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F0FDFA 100%);
            border: 2px solid #2DD4BF;
            border-top: 6px solid #0D9488;
            border-radius: 18px;
            padding: 1.35rem 1.55rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 20px rgba(13, 148, 136, 0.12);
            animation: hqPopIn 0.3s ease-out;
        }}
        .hq-card-blue {{
            background: linear-gradient(135deg, #EFF6FF 0%, #E0E7FF 100%);
            border: 2px solid #93C5FD;
            border-left: 6px solid #4F46E5;
            border-radius: 16px;
            padding: 1.15rem 1.45rem;
            margin-bottom: 1rem;
            animation: hqPopIn 0.28s ease-out;
        }}
        .hq-card-coral {{
            background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%);
            border: 2px solid #FDA4AF;
            border-left: 6px solid #E11D48;
            border-radius: 16px;
            padding: 1.2rem 1.45rem;
            margin-bottom: 1rem;
            animation: hqPopIn 0.28s ease-out;
        }}
        .hq-card-teacher {{
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border: 2px solid #FCD34D;
            border-left: 6px solid #D97706;
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 16px rgba(217, 119, 6, 0.1);
            animation: hqPopIn 0.3s ease-out;
        }}

        /* 화사한 컬러 배지 */
        .hq-badge-teal {{
            display: inline-block; background: linear-gradient(135deg, #CCFBF1, #99F6E4); color: #0F766E !important;
            font-size: 0.8rem; font-weight: 800; padding: 0.24rem 0.72rem; border-radius: 999px; margin-right: 0.35rem;
        }}
        .hq-badge-basic {{
            display: inline-block; background: linear-gradient(135deg, #D1FAE5, #A7F3D0); color: #047857 !important;
            font-size: 0.8rem; font-weight: 800; padding: 0.24rem 0.72rem; border-radius: 999px; margin-right: 0.35rem;
        }}
        .hq-badge-inter {{
            display: inline-block; background: linear-gradient(135deg, #DBEAFE, #BFDBFE); color: #1D4ED8 !important;
            font-size: 0.8rem; font-weight: 800; padding: 0.24rem 0.72rem; border-radius: 999px; margin-right: 0.35rem;
        }}
        .hq-badge-adv {{
            display: inline-block; background: linear-gradient(135deg, #FFEDD5, #FED7AA); color: #C2410C !important;
            font-size: 0.8rem; font-weight: 800; padding: 0.24rem 0.72rem; border-radius: 999px; margin-right: 0.35rem;
        }}
        .hq-badge-coral {{
            display: inline-block; background: linear-gradient(135deg, #FFE4E6, #FECDD3); color: #BE123C !important;
            font-size: 0.8rem; font-weight: 800; padding: 0.24rem 0.72rem; border-radius: 999px; margin-right: 0.35rem;
        }}
        .hq-badge-navy {{
            display: inline-block; background: #EEF2FF; color: #3730A3 !important; border: 1px solid #C7D2FE;
            font-size: 0.8rem; font-weight: 700; padding: 0.22rem 0.7rem; border-radius: 999px; margin-right: 0.35rem;
        }}

        /* 상단 실시간 진도 보드 */
        .hq-tracker-board {{
            background: #FFFFFF;
            border: 2px solid #C7D2FE;
            border-radius: 18px;
            padding: 1.05rem 1.35rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 6px 18px rgba(79, 70, 229, 0.08);
        }}
        .hq-progress-fill {{
            background: linear-gradient(90deg, #4F46E5 0%, #0EA5E9 50%, #10B981 100%);
            background-size: 200% 200%;
            animation: hqShimmer 3s ease infinite;
            height: 100%;
            border-radius: 999px;
            transition: width 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}
        .hq-tracker-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            margin-top: 0.7rem;
        }}
        .hq-step-pill {{
            border-radius: 12px;
            padding: 0.52rem 0.6rem;
            font-size: 0.81rem;
            font-weight: 700;
            text-align: center;
            border: 1.5px solid #E2E8F0;
            background: #F8FAFC;
            color: #64748B !important;
            transition: transform 0.2s ease;
        }}
        .hq-step-pill.done {{
            background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
            border: 2px solid #10B981;
            color: #047857 !important;
            font-weight: 800;
            box-shadow: 0 3px 8px rgba(16, 185, 129, 0.16);
            animation: hqPulseBadge 2.4s ease-in-out infinite;
        }}
        .hq-guide-bar {{
            background: linear-gradient(90deg, #FFFFFF 0%, #EEF2FF 100%);
            border: 2px solid #C7D2FE;
            border-left: 6px solid #4F46E5;
            border-radius: 14px;
            padding: 0.95rem 1.3rem;
            margin-bottom: 1.15rem;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.05);
        }}
        @media (max-width: 768px) {{
            .block-container {{ padding-left: 0.9rem !important; padding-right: 0.9rem !important; }}
            .hq-tracker-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
        {motion_css}
        </style>
        """
    )


def render_sound_effects():
    """
    Web Audio API를 이용해 외부 음원 파일 없이도 경쾌한 버튼 클릭음(통통 튀는 팝 사운드)과
    미션 해결/피드백 완료 시 맑은 효과음(차임벨·팡파르)을 들려주는 사운드 엔진.
    """
    sound_enabled = st.session_state.get("hq_sound_enabled", True)
    pending_sound = st.session_state.pop("hq_pending_sound", None)
    if not sound_enabled:
        return

    sound_type_js = f"'{pending_sound}'" if pending_sound else "null"
    components.html(
        f"""
        <script>
        (function() {{
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;

            function playToneSequence(notes) {{
                try {{
                    const ctx = new AudioCtx();
                    let now = ctx.currentTime;
                    notes.forEach(n => {{
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.type = n.type || 'sine';
                        osc.frequency.setValueAtTime(n.freq, now + (n.delay || 0));
                        gain.gain.setValueAtTime(n.vol || 0.12, now + (n.delay || 0));
                        gain.gain.exponentialRampToValueAtTime(0.001, now + (n.delay || 0) + n.dur);
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.start(now + (n.delay || 0));
                        osc.stop(now + (n.delay || 0) + n.dur);
                    }});
                }} catch (e) {{}}
            }}

            // 1) 이벤트성 효과음 재생 (질문 등록, 정답, 재도전, 완주 팡파르)
            const pending = {sound_type_js};
            if (pending === 'chime') {{
                playToneSequence([
                    {{freq: 523.25, delay: 0, dur: 0.14, vol: 0.13, type: 'triangle'}},
                    {{freq: 659.25, delay: 0.10, dur: 0.16, vol: 0.13, type: 'triangle'}},
                    {{freq: 783.99, delay: 0.20, dur: 0.26, vol: 0.15, type: 'triangle'}}
                ]);
            }} else if (pending === 'success') {{
                playToneSequence([
                    {{freq: 587.33, delay: 0, dur: 0.12, vol: 0.14, type: 'sine'}},
                    {{freq: 739.99, delay: 0.09, dur: 0.14, vol: 0.14, type: 'sine'}},
                    {{freq: 880.00, delay: 0.18, dur: 0.28, vol: 0.16, type: 'triangle'}}
                ]);
            }} else if (pending === 'try_again') {{
                playToneSequence([
                    {{freq: 440.00, delay: 0, dur: 0.14, vol: 0.11, type: 'sine'}},
                    {{freq: 392.00, delay: 0.12, dur: 0.22, vol: 0.11, type: 'sine'}}
                ]);
            }} else if (pending === 'fanfare') {{
                playToneSequence([
                    {{freq: 523.25, delay: 0, dur: 0.13, vol: 0.15, type: 'triangle'}},
                    {{freq: 659.25, delay: 0.11, dur: 0.13, vol: 0.15, type: 'triangle'}},
                    {{freq: 783.99, delay: 0.22, dur: 0.14, vol: 0.15, type: 'triangle'}},
                    {{freq: 1046.50, delay: 0.34, dur: 0.38, vol: 0.18, type: 'triangle'}}
                ]);
            }}

            // 2) 부모 문서의 모든 버튼에 귀여운 '팝(Pop)' 클릭 효과음 연결
            try {{
                const parentDoc = window.parent.document;
                if (!parentDoc._hqClickSoundAttached) {{
                    parentDoc.addEventListener('pointerdown', function(ev) {{
                        const btn = ev.target.closest('button, [ role="radio" ]');
                        if (!btn) return;
                        try {{
                            const ctx = new AudioCtx();
                            const osc = ctx.createOscillator();
                            const gain = ctx.createGain();
                            osc.type = 'sine';
                            osc.frequency.setValueAtTime(620, ctx.currentTime);
                            osc.frequency.exponentialRampToValueAtTime(920, ctx.currentTime + 0.065);
                            gain.gain.setValueAtTime(0.09, ctx.currentTime);
                            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.07);
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.start();
                            osc.stop(ctx.currentTime + 0.075);
                        }} catch (err) {{}}
                    }}, true);
                    parentDoc._hqClickSoundAttached = true;
                }}
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
    )


def render_progress_tracker_board():
    """모든 화면 상단에 실시간 학습 진도율(%)과 5단계 완료 체크를 한눈에 보여주는 스마트 학습지 진도 보드."""
    scen = get_current_scenario_data()
    done_cnt, total_cnt, pct_ratio = get_scenario_progress(scen)
    flags = get_step_completion_flags()
    xp = st.session_state.get("hq_xp", 0)
    pct_int = int(pct_ratio * 100)

    def _pill(label: str, is_done: bool) -> str:
        cls = "hq-step-pill done" if is_done else "hq-step-pill"
        mark = "🌟 완료!" if is_done else "대기"
        return f"<div class='{cls}'>{label}<br><span style='font-size:0.75rem;'>({mark})</span></div>"

    _md_html(
        f"""
        <div class="hq-tracker-board">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                <div>
                    <span class="hq-badge-teal">🚀 실시간 학습 진도율 · {pct_int}%</span>
                    <span class="hq-badge-inter">🎯 모의실습 해결 · {done_cnt} / {total_cnt}단계 (기초·중급·심화)</span>
                    <span class="hq-badge-adv">⭐ 성취 포인트 · {xp} XP</span>
                </div>
                <div style="font-size:0.83rem; color:#475569; font-weight:600;">
                    질문 작성 → 기초·중급·심화 개인 서술 → 팀 협력 & 교사 피드백 순서로 진행할 때마다 진도율이 쑥쑥 올라갑니다!
                </div>
            </div>
            <div style="background:#E0E7FF; height:13px; border-radius:999px; overflow:hidden; margin-top:0.6rem; padding:2px;">
                <div class="hq-progress-fill" style="width:{max(5, pct_int)}%;"></div>
            </div>
            <div class="hq-tracker-grid">
                {_pill("① 단원 질문 (2~3개)", flags["q_done"])}
                {_pill("② 기초 모의실습 (개인)", flags["m1_done"])}
                {_pill("③ 중급 모의실습 (개인)", flags["m2_done"])}
                {_pill("④ 심화 모의실습 (개인)", flags["m3_done"])}
                {_pill("⑤ 팀 협력·교사 피드백", flags["team_done"] and flags["teacher_done"])}
            </div>
        </div>
        """
    )


def render_simple_guide(step_tag: str, now_do: str, why_do: str):
    _md_html(
        f"""
        <div class="hq-guide-bar">
            <div style="font-size:0.97rem;">
                <span class="hq-badge-inter">{step_tag}</span>
                <strong style="color:#0F172A;">{now_do}</strong>
            </div>
            <div style="font-size:0.86rem; color:#475569; margin-top:0.25rem;">
                💡 <strong>수업 설계 의도</strong> · {why_do}
            </div>
        </div>
        """
    )


def render_one_time_notifications():
    badge = st.session_state.pop("hq_pending_badge_notice", None)
    if badge:
        st.success(f"🏅 [역량 배지 획득!] {badge['title']} — {badge['desc']}")

    celeb = st.session_state.pop("hq_pending_celebration", None)
    if celeb:
        if not st.session_state.get("hq_reduce_motion", False):
            st.balloons()
        st.info("🎉 와우! 기초 · 중급 · 심화 3단계 개인 모의실습을 모두 해결했습니다! 이제 [STEP 03 · 팀 협력 & 교사 피드백] 탭으로 이동해 최종 제출을 완성해 보세요.")


# ==============================================================================
# STEP 01: 단원 개념·의학용어 질문(2~3개) & AI 피드백 → 기초·중급·심화 모의실습 3개 제시
# ==============================================================================
def render_unit_inquiry_and_scenario_selection():
    unit = get_current_unit_data()
    unit_name = st.session_state.get("hq_selected_unit", "")
    scen = get_current_scenario_data()
    missions = scen.get("missions", [])
    current_qs = get_unit_questions_for_current()
    sample_qs = unit.get(
        "sample_questions",
        [
            "이 단원의 핵심 의학용어가 실제 환자 간호에서 어떻게 쓰이나요?",
            "응급 보고가 필요한 기준은 무엇인가요?",
            "예비 보건의료인이 주의해야 할 안전 수칙은 무엇인가요?",
        ],
    )

    render_simple_guide(
        step_tag="STEP 01 · 자기주도 질문 & 맞춤 실습 설계",
        now_do="단원의 모르는 개념·의학용어 질문 2~3개를 작성하여 AI 보건튜터 피드백을 받고, 내 수준에 맞춘 [기초·중급·심화] 모의실습 3개를 제시받으세요.",
        why_do="학생이 스스로 질문을 던지며 개념을 먼저 깨우친 뒤, 기초→중급→심화 단계별 PBL 상황으로 나아가야 진정한 자기주도학습이 이루어집니다.",
    )

    # 1) 단원 핵심 의학용어 사전 (클릭형)
    st.markdown("#### 📘 1. 단원 핵심 의학용어 콕콕 짚어보기 (버튼을 눌러보세요!)")
    term_items = list(unit.get("key_terms", {}).items())
    if term_items:
        t_cols = st.columns(len(term_items), gap="small")
        cur_t_idx = min(st.session_state.get("hq_selected_term_idx", 0), len(term_items) - 1)
        for i, (t_name, _) in enumerate(term_items):
            short_name = t_name.split("(")[0].strip()
            with t_cols[i]:
                if st.button(
                    f"🔍 {short_name}",
                    key=f"term_btn_{i}",
                    type="primary" if i == cur_t_idx else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["hq_selected_term_idx"] = i
                    st.session_state["hq_pending_sound"] = "chime"
                    st.rerun()

        sel_t_name, sel_t_desc = term_items[cur_t_idx]
        _md_html(
            f"""
            <div class="hq-card-blue" style="margin-top:0.25rem;">
                <span class="hq-badge-inter">핵심 의학용어 카드</span>
                <strong style="font-size:1.03rem; color:#1E1B4B;">{html.escape(sel_t_name)}</strong>
                <div style="font-size:0.94rem; color:#1E293B; margin-top:0.35rem;">{html.escape(sel_t_desc)}</div>
            </div>
            """
        )

    # 2) 학생 질문 2~3개 입력 폼 & 예시 자동 채우기 버튼
    st.markdown("#### 💬 2. 나의 궁금한 개념·의학용어 질문하기 (2~3개 작성)")
    col_auto, col_caption = st.columns([1.15, 2.1])
    with col_auto:
        if st.button("✨ 단원 추천 질문 3개 자동으로 채우기", type="secondary", use_container_width=True):
            st.session_state[f"q1_{unit['unit_id']}"] = sample_qs[0] if len(sample_qs) > 0 else ""
            st.session_state[f"q2_{unit['unit_id']}"] = sample_qs[1] if len(sample_qs) > 1 else ""
            st.session_state[f"q3_{unit['unit_id']}"] = sample_qs[2] if len(sample_qs) > 2 else ""
            st.session_state["hq_pending_sound"] = "chime"
            st.rerun()
    with col_caption:
        st.caption("※ 직접 궁금한 점을 2~3개 적거나, 왼쪽 [✨ 단원 추천 질문 3개 자동으로 채우기] 버튼을 눌러 수정해 보세요.")

    default_q1 = st.session_state.get(
        f"q1_{unit['unit_id']}",
        current_qs[0]["question"] if len(current_qs) > 0 else sample_qs[0],
    )
    default_q2 = st.session_state.get(
        f"q2_{unit['unit_id']}",
        current_qs[1]["question"] if len(current_qs) > 1 else (sample_qs[1] if len(sample_qs) > 1 else ""),
    )
    default_q3 = st.session_state.get(
        f"q3_{unit['unit_id']}",
        current_qs[2]["question"] if len(current_qs) > 2 else "",
    )

    with st.form("student_questions_form", clear_on_submit=False):
        c_lv1, c_lv2 = st.columns([1.2, 1.8])
        with c_lv1:
            level_choice = st.selectbox(
                "나의 현재 단원 이해 수준 선택",
                [
                    "기초부터 차근차근 (개념 설명 중심)",
                    "표준 (기초→중급→심화 순차 도전)",
                    "심화 (임상 우선순위·응급 판단 중심)",
                ],
                index=1,
            )
        with c_lv2:
            custom_sub = st.text_input(
                "세부 학습 주제 (교과서 내 다른 소단원·질환을 직접 적어도 반영됩니다)",
                value=st.session_state.get("hq_custom_unit_topic", ""),
                placeholder=f"기본값: {unit_name} (또는 원하는 교과서 세부 단원명 입력)",
            )

        q1_in = st.text_input("질문 1 (모르는 의학용어 또는 기본 개념 질문 - 필수)", value=default_q1)
        q2_in = st.text_input("질문 2 (실제 병원 상황에서 궁금한 간호 판단 질문 - 필수)", value=default_q2)
        q3_in = st.text_input("질문 3 (환자안전·응급 대처 등 더 알고 싶은 질문 - 선택)", value=default_q3)

        submit_q_btn = st.form_submit_button(
            "🚀 질문 제출하고 AI 보건튜터 피드백 & 모의실습 3단계(기초·중급·심화) 제시받기",
            type="primary",
            use_container_width=True,
        )

    if submit_q_btn:
        st.session_state[f"q1_{unit['unit_id']}"] = q1_in
        st.session_state[f"q2_{unit['unit_id']}"] = q2_in
        st.session_state[f"q3_{unit['unit_id']}"] = q3_in
        st.session_state["hq_student_level"] = level_choice
        st.session_state["hq_custom_unit_topic"] = custom_sub.strip()
        q_list = [q1_in, q2_in, q3_in]
        entries = submit_student_questions_and_get_feedback(unit, q_list, level_choice, custom_sub)
        if entries:
            st.toast("🎶 질문 피드백과 기초·중급·심화 모의실습 3개가 생성되었습니다! 진도율이 상승했습니다.")
            st.rerun()
        else:
            st.warning("최소 1개 이상의 질문을 입력해 주세요.")

    # 3) AI 보건튜터의 질문별 피드백 출력
    updated_qs = get_unit_questions_for_current()
    if updated_qs:
        st.markdown("#### 🤖 3. 학생 질문에 대한 AI 보건튜터 맞춤 피드백")
        for item in updated_qs:
            _md_html(
                f"""
                <div class="hq-card-selected" style="padding:1.05rem 1.35rem; margin-bottom:0.65rem;">
                    <div>
                        <span class="hq-badge-teal">나의 질문 {item['q_num']}</span>
                        <strong style="font-size:0.98rem;">{html.escape(item['question'])}</strong>
                    </div>
                </div>
                """
            )
            st.markdown(item["feedback_markdown"])

    _md_html("<hr style='margin: 1.4rem 0; border-color: #C7D2FE;'>")

    # 4) 학생의 질문과 수준을 고려해 제시된 모의실습 상황 3개 (기초 · 중급 · 심화)
    st.markdown("#### 🎯 4. 질문과 수준을 반영한 맞춤형 모의실습 상황 3개 (기초 · 중급 · 심화)")
    st.caption("※ 학생의 질문을 바탕으로 구성된 [🟢 기초 → 🔵 중급 → 🟠 심화] 3단계 모의실습입니다. 카드를 확인하고 아래 입체 버튼을 눌러 도전해 보세요!")

    m_cols = st.columns(3, gap="medium")
    badge_classes = ["hq-badge-basic", "hq-badge-inter", "hq-badge-adv"]
    level_icons = ["🟢", "🔵", "🟠"]
    subs = st.session_state.get("hq_submissions", {})

    for idx, m in enumerate(missions):
        is_done = m["id"] in subs
        b_cls = badge_classes[min(idx, 2)]
        lv_icon = level_icons[min(idx, 2)]
        card_cls = "hq-card-selected" if is_done else f"hq-card-level-{min(idx, 2)}"
        status_txt = "🌟 해결 완료!" if is_done else "도전 대기"

        with m_cols[idx]:
            _md_html(
                f"""
                <div class="{card_cls}" style="min-height:250px; display:flex; flex-direction:column; justify-content:space-between;">
                    <div>
                        <div style="margin-bottom:0.5rem;">
                            <span class="{b_cls}">{lv_icon} {html.escape(m.get('level_label', f'단계 {idx+1}'))}</span>
                            <span class="hq-badge-navy">{status_txt}</span>
                        </div>
                        <h4 style="margin:0.2rem 0 0.5rem 0; font-size:1.05rem;">{html.escape(m['title'])}</h4>
                        <p style="font-size:0.89rem; color:#334155; margin-bottom:0.6rem;">
                            {html.escape(m['situation'][:95])}...
                        </p>
                    </div>
                    <div style="font-size:0.82rem; background:#FFFFFF; padding:0.55rem 0.75rem; border-radius:10px; border:1.5px solid #E0E7FF; color:#3730A3;">
                        <strong>🎯 학습목표</strong>: {html.escape(m['learning_objective'][:62])}...
                    </div>
                </div>
                """
            )
            btn_lbl = (
                f"{lv_icon} {m.get('level_label', '실습')} 해결하러 가기 →"
                if not is_done
                else f"✔ {m.get('level_label', '실습')} 결과/피드백 다시 보기"
            )
            if st.button(btn_lbl, key=f"go_mission_{idx}", type="primary" if not is_done else "secondary", use_container_width=True):
                st.session_state["hq_active_mission_idx"] = idx
                st.session_state["hq_nav_view"] = "STEP 02 · 기초·중급·심화 실습"
                st.session_state["hq_pending_sound"] = "chime"
                st.rerun()


# ==============================================================================
# STEP 02: 기초 · 중급 · 심화 모의실습 PBL 자기주도 해결 (개인별 서술 제출 & AI 보건튜터 개인 피드백)
# ==============================================================================
def render_mission_runner():
    scenario = get_current_scenario_data()
    missions = scenario.get("missions", [])
    active_idx = min(st.session_state.get("hq_active_mission_idx", 0), len(missions) - 1)
    mission = missions[active_idx]
    m_id = mission["id"]
    level_label = mission.get("level_label", f"미션 {mission.get('step_num', 1)}")

    existing_sub = st.session_state.get("hq_submissions", {}).get(m_id)

    render_simple_guide(
        step_tag=f"STEP 02 · {level_label} (개인 자기주도 PBL 해결)",
        now_do=f"[{level_label}] 환자 상황과 임상 단서를 분석하여 알맞은 판단을 고르고, 개인별로 해결 방안과 근거를 서술해 AI 보건튜터의 개인 피드백을 받으세요.",
        why_do=mission.get("learning_objective", ""),
    )

    # 기초 -> 중급 -> 심화 상단 선택 버튼
    level_icons = ["🟢", "🔵", "🟠"]
    m_cols = st.columns(len(missions), gap="small")
    for i, m_item in enumerate(missions):
        sub_i = st.session_state.get("hq_submissions", {}).get(m_item["id"])
        lv_name = m_item.get("level_label", f"단계 {i+1}")
        icon_i = level_icons[min(i, 2)]
        done_mark = " 🌟완료" if sub_i else " (도전)"
        with m_cols[i]:
            if st.button(
                f"{icon_i} {i + 1}단계 · {lv_name}{done_mark}",
                key=f"step_m_{m_item['id']}",
                type="primary" if i == active_idx else "secondary",
                use_container_width=True,
            ):
                st.session_state["hq_active_mission_idx"] = i
                st.rerun()

    # [제시문 카드] 모의실습 상황 및 핵심 임상 단서
    clues_html = " &nbsp;·&nbsp; ".join([f"<strong>{html.escape(c)}</strong>" for c in mission.get("clinical_clues", [])])
    badge_cls = "hq-badge-basic" if active_idx == 0 else ("hq-badge-inter" if active_idx == 1 else "hq-badge-adv")
    card_level_cls = f"hq-card-level-{min(active_idx, 2)}"

    _md_html(
        f"""
        <div class="{card_level_cls}" style="margin-top:0.35rem;">
            <div style="margin-bottom:0.5rem;">
                <span class="{badge_cls}">{level_icons[min(active_idx, 2)]} {html.escape(level_label)} ({active_idx + 1} / {len(missions)})</span>
                <span class="hq-badge-navy">{html.escape(mission.get('question_type', 'PBL 문제해결'))}</span>
            </div>
            <h3 style="margin:0.15rem 0 0.7rem 0; font-size:1.26rem;">{html.escape(mission['title'])}</h3>
            <div style="font-size:0.97rem; background:#FFFFFF; padding:1.05rem 1.25rem; border-radius:12px; border:1.5px solid #C7D2FE; margin-bottom:0.75rem;">
                <strong style="color:#312E81;">🏥 가상 병원 임상 상황</strong><br>
                <span style="color:#1E293B;">{html.escape(mission['situation'])}</span>
            </div>
            <div style="font-size:0.91rem; background:#F0FDFA; padding:0.78rem 1.15rem; border-radius:12px; border:1.5px solid #5EEAD4; color:#0F766E;">
                <strong>🔎 PBL 핵심 단서</strong> &nbsp;|&nbsp; {clues_html}
            </div>
        </div>
        """
    )

    c_hint1, c_hint2 = st.columns([1.4, 1])
    with c_hint1:
        with st.expander("💡 판단이 어려울 때 생각 힌트 열기"):
            st.info(mission.get("hint", ""))
    with c_hint2:
        if st.button("✍️ 개인 서술 예시 문장틀 채우기", key=f"fill_rat_{m_id}", type="secondary", use_container_width=True):
            sample_rat = (
                f"환자에게서 '{mission['clinical_clues'][0]}' 단서가 관찰되므로, "
                f"환자 안전과 감염·합병증 예방을 위해 '{mission['options'][mission['correct_index']][:38]}...' 행동을 최우선으로 수행해야 합니다."
            )
            st.session_state[f"rat_{m_id}"] = sample_rat
            st.session_state["hq_pending_sound"] = "chime"
            st.rerun()

    # [개인 자기주도 PBL 해결 폼]
    default_idx = existing_sub["selected_idx"] if existing_sub else 0
    default_rationale = st.session_state.get(f"rat_{m_id}", existing_sub["rationale"] if existing_sub else "")

    with st.form(key=f"form_{m_id}", clear_on_submit=False):
        st.markdown(f"#### Q. {mission['question']}")
        selected_option = st.radio(
            "1) 가장 적절한 간호 판단 선택지 고르기",
            options=list(range(len(mission["options"]))),
            format_func=lambda idx: f"{idx + 1}번. {mission['options'][idx]}",
            index=default_idx,
            key=f"radio_{m_id}",
        )
        st.caption(f"📌 서술 가이드: {mission.get('pbl_writing_guide', '관찰한 단서와 판단 이유를 자신의 말로 서술해 보세요.')}")
        rationale_input = st.text_area(
            f"2) [{level_label}] 개인별 자기주도 PBL 해결방안 및 판단 근거 서술하기",
            value=default_rationale,
            height=95,
            placeholder="예: 환자에게 분비물 노출 단서가 있으므로 교차감염을 막기 위해 흐르는 물과 비누로 40~60초간 손을 씻는 것이 가장 안전합니다.",
        )
        btn_txt = (
            f"🔄 [{level_label}] 개인 서술 수정 제출 및 AI 피드백 다시 받기"
            if existing_sub
            else f"✅ [{level_label}] 개인 해결안 제출 및 AI 보건튜터 개인 피드백 받기"
        )
        submitted = st.form_submit_button(btn_txt, type="primary", use_container_width=True)

    if submitted:
        st.session_state[f"rat_{m_id}"] = rationale_input
        evaluate_mission_submission(mission, selected_option, rationale_input)
        st.toast(f"🎵 {level_label} 개인 제출 및 AI 피드백이 완료되었습니다! 진도율이 반영되었습니다.")
        st.rerun()

    # [제출 후: AI 보건튜터 개인별 피드백 출력]
    sub = st.session_state.get("hq_submissions", {}).get(m_id)
    if sub:
        if sub.get("is_correct"):
            _md_html(
                f"""
                <div class="hq-card-selected">
                    <span class="hq-badge-teal">🌟 개인별 제출 완료 · 정확한 임상 판단!</span>
                    <span class="hq-badge-navy">{html.escape(sub.get('rationale_status', ''))}</span>
                    <h4 style="margin:0.4rem 0; color:#0F766E;">{html.escape(level_label)} 해결 완료 ({sub['selected_idx'] + 1}번 선택)</h4>
                    <div style="font-size:0.93rem; background:#FFFFFF; padding:0.8rem 1.05rem; border-radius:10px; border:1.5px solid #99F6E4; margin-bottom:0.5rem;">
                        <strong>✍️ 나의 개인별 PBL 서술 내용</strong>:<br>
                        "{html.escape(sub.get('rationale') or '(서술 미입력 — 위 서술란에 이유를 적고 다시 제출하면 더 자세한 피드백을 받을 수 있습니다.)')}"
                    </div>
                </div>
                """
            )
        else:
            _md_html(
                f"""
                <div class="hq-card-coral">
                    <span class="hq-badge-coral">💪 재검토 코칭 (감점 없음 · 다시 도전해 보세요!)</span>
                    <h4 style="margin:0.4rem 0; color:#9F1239;">놓친 임상 단서를 확인하고 다시 선택해 보세요</h4>
                    <div style="font-size:0.92rem; background:#FFFFFF; padding:0.75rem 1rem; border-radius:10px; border:1.5px solid #FECDD3;">
                        <strong>나의 서술 내용</strong>: "{html.escape(sub.get('rationale') or '-')}"
                    </div>
                </div>
                """
            )

        st.info(sub.get("ai_individual_feedback", ""))

        with st.expander("📖 1~4번 전체 선택지 상세 해설 및 교과서 참고 출처 확인하기"):
            for idx, exp_text in enumerate(mission.get("option_explanations", [])):
                prefix = "✔ [정답] " if idx == mission.get("correct_index") else f"• [{idx + 1}번] "
                st.markdown(f"**{prefix}{mission['options'][idx]}**\n  - {exp_text}")
            ref_src = mission.get("reference_source", "고등학교 보건간호 교육과정 교과서")
            rev_stat = mission.get("teacher_review_status", mission.get("review_status", "교과서 표준 근거 확인됨"))
            st.caption(f"참고 출처: {ref_src} | 검토 상태: {rev_stat}")

        if active_idx < len(missions) - 1:
            next_lv = missions[active_idx + 1].get("level_label", f"단계 {active_idx + 2}")
            if st.button(f"👉 다음 단계 [{next_lv}] 해결하러 이동하기 →", type="primary", use_container_width=True):
                st.session_state["hq_active_mission_idx"] = active_idx + 1
                st.session_state["hq_pending_sound"] = "chime"
                st.rerun()
        else:
            if st.button("🏆 기초·중급·심화 개인 해결 완료! [STEP 03 · 팀별 협력 & 교사 피드백]으로 이동하기 →", type="primary", use_container_width=True):
                st.session_state["hq_nav_view"] = "STEP 03 · 팀 협력 & 교사 피드백"
                st.session_state["hq_pending_sound"] = "fanfare"
                st.rerun()


# ==============================================================================
# STEP 03: 팀별 협력 서술 제출 → AI 보건튜터 팀 피드백 → 교사 피드백 & 보고서 제출함·인쇄
# ==============================================================================
def _build_printable_activity_sheet_html() -> str:
    """학생 질문(2~3개) + 기초·중급·심화 개인 서술 및 AI 피드백 + 팀 협력 및 AI 팀 피드백 + 교사 최종 피드백이 모두 포함된 디지털 학습지 HTML."""
    unit_name = st.session_state.get("hq_selected_unit", "")
    scenario = get_current_scenario_data()
    completed, total, pct = get_scenario_progress(scenario)
    xp = st.session_state.get("hq_xp", 0)
    student_name = st.session_state.get("hq_student_label", "")
    group_name = st.session_state.get("hq_group_label", "")
    notes = st.session_state.get("hq_team_notes", {})
    qs = get_unit_questions_for_current()

    q_rows = ""
    if qs:
        for q_item in qs:
            q_rows += f"<li><strong>질문 {q_item['q_num']}</strong>: {html.escape(q_item['question'])}</li>"
    else:
        q_rows = "<li>(작성된 단원 질문 없음)</li>"

    m_rows = ""
    for m in scenario.get("missions", []):
        sub = st.session_state.get("hq_submissions", {}).get(m["id"])
        lv = m.get("level_label", f"미션 {m.get('step_num', 1)}")
        if sub:
            choice_str = f"{sub['selected_idx'] + 1}번. {html.escape(sub['selected_text'])}"
            rat_str = html.escape(sub.get("rationale") or "-")
            fb_short = html.escape(sub.get("rationale_status") or "AI 개인 피드백 완료")
        else:
            choice_str = "(미제출)"
            rat_str = "-"
            fb_short = "미제출"

        m_rows += f"""
        <tr>
            <td style="font-weight:700; text-align:center;">{html.escape(lv)}</td>
            <td><strong>{html.escape(m['title'])}</strong><br><span style="font-size:12.5px; color:#334155;">선택: {choice_str}</span></td>
            <td>{rat_str}</td>
            <td style="font-size:12.5px; color:#0F766E;">{fb_short}</td>
        </tr>
        """

    ai_team_fb_clean = html.escape(notes.get("ai_team_feedback") or "(팀 협력 제출 후 자동 생성됩니다)").replace("\n", "<br>")
    teacher_fb_clean = html.escape(notes.get("teacher_feedback") or "(교사 피드백 확인 버튼을 누르면 기록됩니다)").replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>보건간호 스마트 디지털 PBL 학습지</title>
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    body {{
        font-family: 'Pretendard', 'Malgun Gothic', sans-serif;
        color: #1E293B; background: #F8FAFC; margin: 16px; line-height: 1.55; word-break: keep-all;
    }}
    .sheet {{
        max-width: 860px; margin: 0 auto; background: #FFFFFF; border: 2px solid #C7D2FE;
        border-top: 6px solid #4F46E5; border-radius: 16px; padding: 24px 28px;
        box-shadow: 0 4px 16px rgba(79, 70, 229, 0.08);
    }}
    .top-bar {{
        display: flex; justify-content: space-between; align-items: flex-end;
        border-bottom: 2px solid #E0E7FF; padding-bottom: 12px; margin-bottom: 14px;
    }}
    h1 {{ margin: 0; font-size: 20px; color: #1E1B4B; }}
    h2 {{
        font-size: 14.5px; color: #3730A3; margin: 16px 0 6px 0;
        padding-left: 8px; border-left: 4px solid #4F46E5;
    }}
    .meta {{
        display: grid; grid-template-columns: 1fr 1fr; gap: 6px 16px;
        background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 10px;
        padding: 10px 14px; font-size: 13px; margin-bottom: 14px;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border: 1px solid #CBD5E1; padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #EEF2FF; color: #312E81; font-weight: 700; }}
    .box {{
        background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 10px;
        padding: 10px 14px; font-size: 13px; margin-bottom: 10px;
    }}
    .teacher-box {{
        background: #FFFBEB; border: 1.5px solid #FCD34D; border-radius: 10px;
        padding: 10px 14px; font-size: 13px;
    }}
    .print-btn {{
        background: linear-gradient(135deg, #4F46E5, #0EA5E9); color: #FFFFFF; border: none; border-radius: 10px;
        padding: 8px 16px; font-size: 13.5px; font-weight: 700; cursor: pointer;
    }}
    @media print {{ .no-print {{ display: none !important; }} body {{ margin: 0; background: #FFFFFF; }} }}
</style>
</head>
<body>
<div class="sheet">
    <div class="top-bar">
        <div>
            <h1>{html.escape(SITE_CONFIG['site_title'])} — PBL 디지털 학습 결과지</h1>
            <div style="font-size:12.5px; color:#64748B;">자기주도 질문 → 기초·중급·심화 개인 PBL → 팀 협력 → AI 튜터 & 교사 피드백 통합 기록표</div>
        </div>
        <div class="no-print">
            <button class="print-btn" onclick="window.print()">🖨️ 지금 바로 인쇄 / PDF로 저장</button>
        </div>
    </div>
    <div class="meta">
        <div><strong>학번 / 이름</strong>: {html.escape(student_name or '미입력')}</div>
        <div><strong>모둠명</strong>: {html.escape(group_name or '미입력')}</div>
        <div><strong>학습 단원</strong>: {html.escape(unit_name)}</div>
        <div><strong>학습 진도율</strong>: {int(pct * 100)}% ({completed}/{total}단계 완료 · {xp} XP)</div>
    </div>

    <h2>1. 나의 단원 질문 (2~3개) 및 AI 보건튜터 개념 피드백 완료</h2>
    <div class="box"><ul style="margin:0; padding-left:18px;">{q_rows}</ul></div>

    <h2>2. 기초 · 중급 · 심화 모의실습 개인별 PBL 해결 서술 및 AI 개인 피드백</h2>
    <table>
        <thead>
            <tr>
                <th style="width:14%; text-align:center;">실습 단계</th>
                <th style="width:32%;">모의실습 상황 및 나의 선택</th>
                <th style="width:34%;">개인별 자기주도 PBL 해결 서술</th>
                <th style="width:20%;">AI 보건튜터 개인 피드백</th>
            </tr>
        </thead>
        <tbody>{m_rows}</tbody>
    </table>

    <h2>3. 팀별 협력 해결안 최종 서술 및 AI 보건튜터 팀 피드백</h2>
    <div class="box">
        <div><strong>• 개인별 해결안 요약</strong>: {html.escape(notes.get('individual_summary') or '-')}</div>
        <div><strong>• 모둠원 의견 비교</strong>: {html.escape(notes.get('peer_comparison') or '-')}</div>
        <div><strong>• 팀 최종 해결안 및 우선순위 근거</strong>: {html.escape(notes.get('team_conclusion') or '-')}</div>
        <div><strong>• 토의 후 성장 성찰</strong>: {html.escape(notes.get('thought_change') or '-')}</div>
        <hr style="border:none; border-top:1px dashed #CBD5E1; margin:8px 0;">
        <div style="color:#0F766E;">{ai_team_fb_clean}</div>
    </div>

    <h2>4. 담당 교사 최종 피드백</h2>
    <div class="teacher-box">
        <strong>👩‍🏫 교사 종합 코멘트</strong><br>{teacher_fb_clean}
    </div>
</div>
</body>
</html>"""


def render_collaboration_and_growth():
    scenario = get_current_scenario_data()
    missions = scenario.get("missions", [])
    subs = st.session_state.get("hq_submissions", {})
    notes = st.session_state.get("hq_team_notes", {})

    render_simple_guide(
        step_tag="STEP 03 · 팀별 협력 제출 & AI·교사 피드백 완성",
        now_do="기초·중급·심화 개인 서술 내용을 바탕으로 팀별 협력 해결안을 작성해 [AI 보건튜터 팀 피드백]을 받고, 마지막으로 [교사 피드백]을 확인해 선생님께 최종 보고서를 제출하세요.",
        why_do="개인 자기주도학습 → 팀 협력 문제해결 → AI 튜터 피드백 → 교사 최종 피드백으로 이어지는 완전학습 루프를 완성합니다.",
    )

    auto_ind_lines = []
    for m in missions:
        s = subs.get(m["id"])
        lv = m.get("level_label", f"단계 {m.get('step_num', 1)}")
        if s and s.get("rationale"):
            auto_ind_lines.append(f"[{lv}] {s['rationale']}")
        elif s:
            auto_ind_lines.append(f"[{lv}] {s['selected_idx']+1}번 선택 완료")
    auto_ind_summary = (
        " / ".join(auto_ind_lines)
        if auto_ind_lines
        else "기초·중급·심화 모의실습에서 환자 안전과 관찰·보고 원칙에 따라 간호 우선순위를 판단함."
    )

    st.markdown("#### 🤝 1. 개인별 서술 종합 및 팀별 협력 해결안 최종 제출")
    c_fill, c_cap = st.columns([1.15, 2.1])
    with c_fill:
        if st.button("✨ 팀 협력 서술 예시 문장틀 자동 채우기", type="secondary", use_container_width=True):
            st.session_state["hq_team_notes"]["individual_summary"] = auto_ind_summary
            st.session_state["hq_team_notes"]["peer_comparison"] = (
                "나는 기초·중급 단계의 개별 처치 절차에 집중했는데, 팀원들은 주변 환자 분리와 손상성 폐기물 즉시 처리 등 환경 안전 단서까지 함께 짚어주었다."
            )
            st.session_state["hq_team_notes"]["team_conclusion"] = (
                "1순위: 표준주의 보호구 착용 및 환자·주변 안전 확보 → 2순위: 정확한 활력징후·증상 사정 후 담당 간호사·의사 즉시 보고 → 3순위: 침습적 처치 금지 및 환자 안정·교육 시행"
            )
            st.session_state["hq_team_notes"]["thought_change"] = (
                "혼자 판단할 때 놓치기 쉬운 임상 단서를 팀원들과 비교하며 훨씬 안전한 간호 우선순위를 세울 수 있었고, 예비 의료인의 법적 업무 경계를 명확히 깨달았다."
            )
            st.session_state["hq_pending_sound"] = "chime"
            st.rerun()
    with c_cap:
        st.caption("※ 기초·중급·심화에서 작성한 나의 개인 서술이 아래 ①번 칸에 자동 연동됩니다.")

    with st.form("team_collab_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            s_name_in = st.text_input("학번 및 이름 (필수)", value=st.session_state.get("hq_student_label", ""), placeholder="예: 2학년 1반 홍길동")
        with c2:
            g_name_in = st.text_input("팀(모둠) 이름", value=st.session_state.get("hq_group_label", ""), placeholder="예: 나이팅게일 1모둠")

        ind_sum_in = st.text_area(
            "① [개인별 서술 종합] 기초·중급·심화 모의실습에서 내가 작성한 핵심 해결 내용",
            value=notes.get("individual_summary") or auto_ind_summary,
            height=68,
        )
        peer_comp_in = st.text_input(
            "② [팀원과 근거 비교] 내 생각과 팀원들의 생각은 어떤 점이 같거나 달랐나요?",
            value=notes.get("peer_comparison", ""),
            placeholder="예: 나는 손 씻기만 생각했는데 팀원은 환자 간 거리 확보와 즉시 보고까지 제시해 주었다.",
        )
        team_conc_in = st.text_area(
            "③ [팀별 협력 최종 해결안] 기초·중급·심화를 종합하여 우리 팀이 합의한 최종 간호 우선순위와 근거",
            value=notes.get("team_conclusion", ""),
            height=78,
            placeholder="예: 1순위 보호구 착용 및 감염 차단 → 2순위 환자 증상 관찰 및 즉시 보고 → 3순위 비침습적 안정 간호",
        )
        thought_chg_in = st.text_input(
            "④ [협력 성찰] 개인 학습 후 팀 토의를 거치며 새롭게 깨닫거나 성장한 점",
            value=notes.get("thought_change", ""),
            placeholder="예: 응급 상황일수록 기본 원칙을 생략하지 않고 팀원들과 단서를 교차 확인해야 환자가 안전하다는 점을 배웠다.",
        )

        team_sub_btn = st.form_submit_button(
            "✅ 팀별 협력 해결안 최종 제출 및 AI 보건튜터 팀 피드백 받기",
            type="primary",
            use_container_width=True,
        )

    if team_sub_btn:
        submit_team_collaboration_and_get_feedback(
            student_name=s_name_in,
            group_name=g_name_in,
            individual_summary=ind_sum_in,
            peer_comparison=peer_comp_in,
            team_conclusion=team_conc_in,
            thought_change=thought_chg_in,
        )
        st.toast("🎶 팀별 협력 해결안이 제출되어 AI 보건튜터 팀 피드백이 생성되었습니다!")
        st.rerun()

    updated_notes = st.session_state.get("hq_team_notes", {})
    if updated_notes.get("ai_team_feedback"):
        st.markdown("#### 🤖 2. 팀별 제출 내용에 대한 AI 보건튜터 피드백")
        st.info(updated_notes["ai_team_feedback"])

    _md_html("<hr style='margin: 1.3rem 0; border-color: #C7D2FE;'>")

    # 3) 마지막 단계: 교사의 피드백 받기 및 선생님 제출함에 등록
    st.markdown("#### 👩‍🏫 3. 마지막 단계: 담당 교사 피드백 받기 & 선생님께 보고서 제출하기")
    st.caption("※ 개인별 AI 피드백과 팀별 AI 피드백을 확인한 뒤 아래 버튼을 누르면 교사 종합 피드백이 기록되고 선생님의 제출 관리함에 자동 등록됩니다.")

    col_t1, col_t2 = st.columns([1.25, 1.75])
    with col_t1:
        if st.button("📤 선생님께 최종 보고서 제출 & 교사 피드백 확인하기", type="primary", use_container_width=True):
            entry = submit_final_report_to_teacher()
            if not st.session_state.get("hq_reduce_motion", False):
                st.balloons()
            st.toast(f"🎉 [{entry['student_name']}] 학생의 최종 보고서가 교사용 제출함에 저장되었습니다!")
            st.rerun()
    with col_t2:
        with st.expander("👩‍🏫 교사용 직접 코멘트 입력/수정 (선생님 전용)"):
            custom_t = st.text_area(
                "교사 지도 코멘트 직접 입력",
                value=updated_notes.get("teacher_feedback", ""),
                placeholder="학생 개인 서술과 팀 협력 결과에 대한 선생님의 피드백을 입력하면 학습지에 그대로 인쇄됩니다.",
            )
            if st.button("교사 코멘트 적용하기", type="secondary"):
                generate_or_save_teacher_feedback(custom_t)
                st.rerun()

    updated_notes = st.session_state.get("hq_team_notes", {})
    if updated_notes.get("teacher_feedback"):
        _md_html(
            f"""
            <div class="hq-card-teacher">
                <span class="hq-badge-adv">🌟 담당 교사 최종 피드백 & 보고서 등록 완료</span>
                <h4 style="margin:0.35rem 0; color:#92400E;">👩‍🏫 교사 종합 지도 피드백</h4>
                <div style="font-size:0.94rem; color:#1E293B;">{html.escape(updated_notes['teacher_feedback'])}</div>
            </div>
            """
        )

    _md_html("<hr style='margin: 1.3rem 0; border-color: #C7D2FE;'>")

    # 4) 완성된 스마트 디지털 학습지 저장·인쇄 & 교사용 제출물 통합 관리함
    st.markdown("#### 🖨️ 4. 완성된 스마트 디지털 학습지 저장·인쇄 및 교사용 제출물 관리함")
    sheet_html = _build_printable_activity_sheet_html()

    d_col1, d_col2 = st.columns(2, gap="medium")
    with d_col1:
        st.download_button(
            label="📥 학생용: 내 디지털 학습지 결과 파일(.html) 저장하기",
            data=sheet_html,
            file_name=f"보건간호_PBL_디지털학습지_{st.session_state.get('hq_student_label') or '학생'}.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )
    with d_col2:
        csv_bytes = export_submitted_reports_csv()
        reports_cnt = len(load_submitted_reports())
        st.download_button(
            label=f"📊 교사용: 제출된 학생 보고서 전체 엑셀(CSV) 다운로드 ({reports_cnt}명)",
            data=csv_bytes,
            file_name="HEALTH_QUEST_학생제출보고서_전체목록.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander(f"📂 [교사용 제출물 통합 관리함 열기] 현재 제출 완료된 학생 보고서 ({reports_cnt}건 확인 및 관리)"):
        all_reps = load_submitted_reports()
        if not all_reps:
            st.caption("아직 제출된 보고서가 없습니다. 위 [📤 선생님께 최종 보고서 제출 & 교사 피드백 확인하기] 버튼을 누르면 즉시 이곳에 집계됩니다.")
        else:
            st.caption("※ 학생이 제출한 학번/이름, 단원, 진도율, 질문(2~3개), 기초·중급·심화 서술, 팀 최종 해결안이 자동 기록됩니다. 상단 [엑셀(CSV) 다운로드] 버튼으로 한 번에 내려받아 수행평가 채점에 활용하세요.")
            for idx, r in enumerate(reversed(all_reps), start=1):
                _md_html(
                    f"""
                    <div class="hq-card" style="padding:0.9rem 1.2rem; margin-bottom:0.55rem;">
                        <div style="display:flex; justify-content:space-between; flex-wrap:wrap;">
                            <div>
                                <span class="hq-badge-teal">#{idx} · {html.escape(r.get('student_name', ''))} ({html.escape(r.get('group_name', ''))})</span>
                                <span class="hq-badge-inter">{html.escape(r.get('unit_name', ''))}</span>
                                <span class="hq-badge-adv">진도율 {r.get('progress_pct', 0)}% · {r.get('xp', 0)} XP</span>
                            </div>
                            <div style="font-size:0.8rem; color:#64748B;">제출일시: {html.escape(r.get('submitted_at', ''))}</div>
                        </div>
                        <div style="font-size:0.86rem; color:#334155; margin-top:0.35rem;">
                            <strong>• 기초/중급/심화 서술</strong>: {html.escape(r.get('basic_mission', '')[:60])}...<br>
                            <strong>• 팀 최종 해결안</strong>: {html.escape(r.get('team_conclusion', '') or '(미입력)')}
                        </div>
                    </div>
                    """
                )

    components.html(sheet_html, height=680, scrolling=True)
