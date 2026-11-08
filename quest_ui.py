"""HEALTH QUEST — 트렌디 에듀테크 스마트 학습지 UI·UX 모듈
- 폰트: 네이버 나눔스퀘어라운드(NanumSquareRound, OFL 공공 무료) & 지마켓 산스(GmarketSans, 공공·상업 완전 무료)
- 특징: 3열 카드 높이 완벽 고정(Pixel-Perfect Equal Height), 간결한 마이크로카피, 입체 3D 버튼 애니메이션, 효과음, 교사용 제출함
"""
import html
import random
import re
import streamlit as st
import streamlit.components.v1 as components
from quest_data import SITE_CONFIG
from quest_engine import (
    evaluate_mission_submission,
    export_submitted_reports_csv,
    generate_or_save_teacher_feedback,
    get_current_scenario_data,
    get_current_unit_data,
    get_scenario_progress,
    get_step_completion_flags,
    get_unit_questions_for_current,
    load_submitted_reports,
    submit_final_report_to_teacher,
    submit_student_questions_and_get_feedback,
    submit_team_collaboration_and_get_feedback,
)


def _md_html(raw_html: str):
    """모든 HTML 줄의 앞뒤 공백을 제거하여 마크다운 코드블록(</div> 노출) 버그를 원천 차단합니다."""
    cleaned = "\n".join(line.strip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def _clean_mission_title(title: str) -> str:
    """제목 앞의 중복된 [기초], [중급], [심화] 말머리를 제거해 카드 제목을 깔끔하게 정리합니다."""
    return re.sub(r"^\[(기초|중급|심화)\]\s*", "", (title or "").strip())


def inject_quest_css(reduce_motion: bool = False):
    """
    공공·교육 현장에서 저작권 걱정 없이 100% 무료로 사용 가능한
    '네이버 나눔스퀘어라운드(OFL 1.1)'와 '지마켓 산스(무료 공개 라이선스)'를 적용한 트렌디 디지털 학습지 스타일.
    """
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
        /* 공공 무료 저작권 안심 폰트 1: 네이버 나눔스퀘어라운드 (OFL 1.1 라이선스) */
        @font-face {{
            font-family: 'NanumSquareRound';
            src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_two@1.0/NanumSquareRound.woff') format('woff');
            font-weight: normal;
            font-style: normal;
            font-display: swap;
        }}
        /* 공공 무료 저작권 안심 폰트 2: 지마켓 산스 (누구나 제한 없이 사용 가능한 무료 폰트) */
        @font-face {{
            font-family: 'GmarketSansMedium';
            src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.woff') format('woff');
            font-weight: normal;
            font-style: normal;
            font-display: swap;
        }}

        :root {{
            color-scheme: light !important;
        }}
        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background: linear-gradient(155deg, #F5F7FF 0%, #F0FDF9 52%, #FFFDF5 100%) !important;
            background-attachment: fixed !important;
            color: #1E293B !important;
            font-family: 'NanumSquareRound', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
            letter-spacing: -0.01em !important;
            overflow-x: hidden !important;
        }}
        .block-container {{
            max-width: 1120px !important;
            margin: 0 auto !important;
            padding-top: 1.2rem !important;
            padding-bottom: 3rem !important;
            padding-left: 1.8rem !important;
            padding-right: 1.8rem !important;
        }}
        header[data-testid="stHeader"] {{
            background: rgba(255, 255, 255, 0.85) !important;
            backdrop-filter: blur(8px);
            border-bottom: 1px solid #E2E8F0;
        }}
        .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown {{
            color: #1E293B !important;
            font-family: 'NanumSquareRound', 'Malgun Gothic', sans-serif !important;
            line-height: 1.65 !important;
            word-break: keep-all !important;
        }}
        h1, h2, h3, h4 {{
            color: #0F172A !important;
            font-family: 'GmarketSansMedium', 'NanumSquareRound', sans-serif !important;
            letter-spacing: -0.02em !important;
            line-height: 1.35 !important;
            word-break: keep-all !important;
        }}

        /* 키프레임 애니메이션 */
        @keyframes hqPopIn {{
            0% {{ opacity: 0; transform: translateY(8px) scale(0.99); }}
            100% {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        @keyframes hqShimmer {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        /* 상단 히어로 배너 (파스텔 바이올렛-스카이-민트 그라데이션) */
        .hq-hero-banner {{
            background: linear-gradient(135deg, #6366F1 0%, #3B82F6 50%, #14B8A6 100%);
            border-radius: 22px;
            padding: 1.2rem 1.6rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 10px 24px rgba(99, 102, 241, 0.2);
            animation: hqPopIn 0.3s ease-out;
        }}
        .hq-hero-banner h1 {{
            color: #FFFFFF !important;
            margin: 0.25rem 0 0 0 !important;
            font-size: 1.62rem !important;
            font-weight: 700 !important;
        }}
        .hq-hero-sub {{
            color: #E0F2FE !important;
            font-size: 0.88rem !important;
            margin-top: 0.15rem !important;
        }}
        .hq-hero-pill {{
            display: inline-block;
            background: rgba(255, 255, 255, 0.24);
            border: 1px solid rgba(255, 255, 255, 0.45);
            color: #FFFFFF !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.2rem 0.72rem;
            border-radius: 999px;
            margin-right: 0.35rem;
        }}

        /* 사이드바 카드 및 텍스트 색상 보호 */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F5F7FF 100%) !important;
            border-right: 1.5px solid #E0E7FF;
        }}
        .hq-sidebar-brand {{
            background: linear-gradient(135deg, #6366F1 0%, #3B82F6 100%);
            padding: 0.9rem 1rem;
            border-radius: 16px;
            margin-bottom: 0.4rem;
            box-shadow: 0 6px 14px rgba(99, 102, 241, 0.22);
        }}
        .hq-sidebar-brand, .hq-sidebar-brand * {{
            color: #FFFFFF !important;
        }}

        /* 입력창 디자인 */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"],
        div[data-baseweb="base-input"],
        textarea,
        input[type="text"] {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 2px solid #DBEAFE !important;
            border-radius: 14px !important;
            -webkit-text-fill-color: #0F172A !important;
            font-family: 'NanumSquareRound', sans-serif !important;
            font-size: 0.94rem !important;
            transition: all 0.16s ease !important;
        }}
        textarea:focus,
        input[type="text"]:focus {{
            border-color: #6366F1 !important;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15) !important;
        }}

        /* 폼 컨테이너 */
        [data-testid="stForm"] {{
            background: #FFFFFF !important;
            border: 2px solid #E0E7FF !important;
            border-top: 5px solid #6366F1 !important;
            border-radius: 20px !important;
            padding: 1.3rem 1.5rem !important;
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.06);
        }}

        /* ==============================================================
           입체 3D 인터랙티브 버튼 (통통 튀는 호버 & 클릭 시 쏙 눌리는 효과)
           ============================================================== */
        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"],
        div.stDownloadButton > button {{
            background: linear-gradient(135deg, #6366F1 0%, #3B82F6 55%, #14B8A6 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 14px !important;
            font-family: 'GmarketSansMedium', 'NanumSquareRound', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            height: 46px !important;
            padding: 0 1.1rem !important;
            box-shadow: 0 4px 0 #4338CA, 0 8px 16px rgba(99, 102, 241, 0.24) !important;
            transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.15s ease !important;
        }}
        div.stButton > button[kind="primary"] *,
        div.stFormSubmitButton > button[kind="primary"] *,
        div.stDownloadButton > button * {{
            color: #FFFFFF !important;
        }}
        div.stButton > button[kind="primary"]:hover,
        div.stFormSubmitButton > button[kind="primary"]:hover,
        div.stDownloadButton > button:hover {{
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 7px 0 #4338CA, 0 12px 22px rgba(59, 130, 246, 0.32) !important;
        }}
        div.stButton > button[kind="primary"]:active,
        div.stFormSubmitButton > button[kind="primary"]:active,
        div.stDownloadButton > button:active {{
            transform: translateY(3px) scale(0.97) !important;
            box-shadow: 0 1px 0 #4338CA, 0 3px 6px rgba(99, 102, 241, 0.2) !important;
        }}

        div.stButton > button[kind="secondary"] {{
            background: #FFFFFF !important;
            color: #3730A3 !important;
            border: 2px solid #C7D2FE !important;
            border-radius: 14px !important;
            font-family: 'GmarketSansMedium', 'NanumSquareRound', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
            height: 46px !important;
            padding: 0 1rem !important;
            box-shadow: 0 4px 0 #CBD5E1, 0 4px 10px rgba(15, 23, 42, 0.04) !important;
            transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.15s ease, background-color 0.15s ease !important;
        }}
        div.stButton > button[kind="secondary"] * {{
            color: #3730A3 !important;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            background: #EEF2FF !important;
            border-color: #6366F1 !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 0 #A5B4FC, 0 10px 18px rgba(99, 102, 241, 0.16) !important;
        }}
        div.stButton > button[kind="secondary"]:active {{
            transform: translateY(3px) scale(0.97) !important;
            box-shadow: 0 1px 0 #A5B4FC !important;
        }}

        /* ==============================================================
           3열 모의실습 카드: 높이·줄수 완벽 균형 고정 (Equal Height Cards)
           ============================================================== */
        .hq-equal-card {{
            height: 238px !important;
            border-radius: 20px;
            padding: 1.15rem 1.25rem;
            margin-bottom: 0.65rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: hqPopIn 0.3s ease-out;
        }}
        .hq-equal-card:hover {{
            transform: translateY(-4px);
        }}
        .hq-theme-0 {{
            background: linear-gradient(180deg, #FFFFFF 0%, #ECFDF5 100%);
            border: 2px solid #6EE7B7;
            border-top: 6px solid #10B981;
            box-shadow: 0 8px 18px rgba(16, 185, 129, 0.09);
        }}
        .hq-theme-1 {{
            background: linear-gradient(180deg, #FFFFFF 0%, #EFF6FF 100%);
            border: 2px solid #93C5FD;
            border-top: 6px solid #3B82F6;
            box-shadow: 0 8px 18px rgba(59, 130, 246, 0.09);
        }}
        .hq-theme-2 {{
            background: linear-gradient(180deg, #FFFFFF 0%, #FFF7ED 100%);
            border: 2px solid #FDBA74;
            border-top: 6px solid #F97316;
            box-shadow: 0 8px 18px rgba(249, 115, 22, 0.09);
        }}
        .hq-theme-done {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F0FDFA 100%);
            border: 2px solid #2DD4BF;
            border-top: 6px solid #0D9488;
            box-shadow: 0 8px 18px rgba(13, 148, 136, 0.12);
        }}
        .hq-eq-title {{
            font-family: 'GmarketSansMedium', 'NanumSquareRound', sans-serif !important;
            font-size: 1.02rem !important;
            font-weight: 700 !important;
            color: #0F172A !important;
            margin: 0.35rem 0 0.35rem 0 !important;
            line-height: 1.35 !important;
            height: 2.7em !important;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .hq-eq-desc {{
            font-size: 0.87rem !important;
            color: #475569 !important;
            margin: 0 !important;
            line-height: 1.5 !important;
            height: 3.0em !important;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .hq-eq-goal {{
            font-size: 0.8rem !important;
            background: rgba(255, 255, 255, 0.9);
            padding: 0.45rem 0.7rem;
            border-radius: 10px;
            border: 1.5px solid #E2E8F0;
            color: #334155 !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* 일반 학습 카드 */
        .hq-card {{
            background: #FFFFFF;
            border: 2px solid #E0E7FF;
            border-radius: 18px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 6px 16px rgba(99, 102, 241, 0.05);
        }}
        .hq-card-selected {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F0FDFA 100%);
            border: 2px solid #5EEAD4;
            border-left: 6px solid #14B8A6;
            border-radius: 16px;
            padding: 1rem 1.3rem;
            margin-bottom: 0.75rem;
        }}
        .hq-card-blue {{
            background: linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%);
            border: 2px solid #BFDBFE;
            border-left: 6px solid #4F46E5;
            border-radius: 16px;
            padding: 1rem 1.35rem;
            margin-bottom: 0.9rem;
        }}
        .hq-card-coral {{
            background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%);
            border: 2px solid #FDA4AF;
            border-left: 6px solid #F43F5E;
            border-radius: 16px;
            padding: 1rem 1.35rem;
            margin-bottom: 0.9rem;
        }}
        .hq-card-teacher {{
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border: 2px solid #FCD34D;
            border-left: 6px solid #F59E0B;
            border-radius: 16px;
            padding: 1.15rem 1.4rem;
            margin-bottom: 0.9rem;
        }}

        /* 파스텔 캡슐 배지 */
        .hq-badge-teal {{
            display: inline-block; background: #CCFBF1; color: #0F766E !important;
            font-size: 0.78rem; font-weight: 800; padding: 0.2rem 0.68rem; border-radius: 999px; margin-right: 0.3rem;
        }}
        .hq-badge-basic {{
            display: inline-block; background: #D1FAE5; color: #047857 !important;
            font-size: 0.78rem; font-weight: 800; padding: 0.2rem 0.68rem; border-radius: 999px; margin-right: 0.3rem;
        }}
        .hq-badge-inter {{
            display: inline-block; background: #DBEAFE; color: #1D4ED8 !important;
            font-size: 0.78rem; font-weight: 800; padding: 0.2rem 0.68rem; border-radius: 999px; margin-right: 0.3rem;
        }}
        .hq-badge-adv {{
            display: inline-block; background: #FFEDD5; color: #C2410C !important;
            font-size: 0.78rem; font-weight: 800; padding: 0.2rem 0.68rem; border-radius: 999px; margin-right: 0.3rem;
        }}
        .hq-badge-coral {{
            display: inline-block; background: #FFE4E6; color: #BE123C !important;
            font-size: 0.78rem; font-weight: 800; padding: 0.2rem 0.68rem; border-radius: 999px; margin-right: 0.3rem;
        }}
        .hq-badge-navy {{
            display: inline-block; background: #EEF2FF; color: #4338CA !important;
            font-size: 0.76rem; font-weight: 700; padding: 0.18rem 0.62rem; border-radius: 999px;
        }}

        /* 상단 컴팩트 진도 보드 */
        .hq-tracker-board {{
            background: #FFFFFF;
            border: 2px solid #E0E7FF;
            border-radius: 18px;
            padding: 0.9rem 1.25rem;
            margin-bottom: 0.95rem;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.06);
        }}
        .hq-progress-fill {{
            background: linear-gradient(90deg, #6366F1 0%, #3B82F6 50%, #10B981 100%);
            background-size: 200% 200%;
            animation: hqShimmer 3s ease infinite;
            height: 100%;
            border-radius: 999px;
            transition: width 0.4s ease;
        }}
        .hq-tracker-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            margin-top: 0.55rem;
        }}
        .hq-step-pill {{
            border-radius: 12px;
            padding: 0.42rem 0.5rem;
            font-size: 0.8rem;
            font-weight: 700;
            text-align: center;
            border: 1.5px solid #E2E8F0;
            background: #F8FAFC;
            color: #64748B !important;
        }}
        .hq-step-pill.done {{
            background: #ECFDF5;
            border: 2px solid #10B981;
            color: #047857 !important;
            font-weight: 800;
        }}
        .hq-guide-bar {{
            background: #FFFFFF;
            border: 2px solid #E0E7FF;
            border-left: 6px solid #6366F1;
            border-radius: 14px;
            padding: 0.75rem 1.15rem;
            margin-bottom: 1rem;
        }}
        @media (max-width: 768px) {{
            .block-container {{ padding-left: 0.9rem !important; padding-right: 0.9rem !important; }}
            .hq-tracker-grid {{ grid-template-columns: 1fr 1fr; }}
            .hq-equal-card {{ height: auto !important; min-height: 220px !important; }}
        }}
        {motion_css}
        </style>
        """
    )


def render_sound_effects():
    """버튼 클릭 및 미션 완료 시(`hq_pending_sound`) 경쾌한 Web Audio API 효과음을 재생합니다."""
    sound_enabled = st.session_state.get("hq_sound_enabled", True)
    pending_sound = st.session_state.pop("hq_pending_sound", None)
    if not sound_enabled or not pending_sound:
        return

    nonce = random.randint(1000, 999999)
    components.html(
        f"""
        <script>
        (function() {{
            // nonce: {nonce}
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
                        gain.gain.setValueAtTime(n.vol || 0.13, now + (n.delay || 0));
                        gain.gain.exponentialRampToValueAtTime(0.001, now + (n.delay || 0) + n.dur);
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.start(now + (n.delay || 0));
                        osc.stop(now + (n.delay || 0) + n.dur);
                    }});
                }} catch (e) {{}}
            }}
            const pending = '{pending_sound}';
            if (pending === 'pop') {{
                playToneSequence([
                    {{freq: 660, delay: 0, dur: 0.06, vol: 0.12, type: 'sine'}},
                    {{freq: 880, delay: 0.05, dur: 0.08, vol: 0.12, type: 'sine'}}
                ]);
            }} else if (pending === 'chime') {{
                playToneSequence([
                    {{freq: 523.25, delay: 0, dur: 0.12, vol: 0.14, type: 'triangle'}},
                    {{freq: 659.25, delay: 0.09, dur: 0.14, vol: 0.14, type: 'triangle'}},
                    {{freq: 783.99, delay: 0.18, dur: 0.22, vol: 0.15, type: 'triangle'}}
                ]);
            }} else if (pending === 'success') {{
                playToneSequence([
                    {{freq: 587.33, delay: 0, dur: 0.11, vol: 0.15, type: 'sine'}},
                    {{freq: 739.99, delay: 0.09, dur: 0.13, vol: 0.15, type: 'sine'}},
                    {{freq: 880.00, delay: 0.18, dur: 0.25, vol: 0.17, type: 'triangle'}}
                ]);
            }} else if (pending === 'try_again') {{
                playToneSequence([
                    {{freq: 440.00, delay: 0, dur: 0.12, vol: 0.12, type: 'sine'}},
                    {{freq: 392.00, delay: 0.11, dur: 0.18, vol: 0.12, type: 'sine'}}
                ]);
            }} else if (pending === 'fanfare') {{
                playToneSequence([
                    {{freq: 523.25, delay: 0, dur: 0.12, vol: 0.15, type: 'triangle'}},
                    {{freq: 659.25, delay: 0.10, dur: 0.12, vol: 0.15, type: 'triangle'}},
                    {{freq: 783.99, delay: 0.20, dur: 0.13, vol: 0.15, type: 'triangle'}},
                    {{freq: 1046.50, delay: 0.31, dur: 0.34, vol: 0.18, type: 'triangle'}}
                ]);
            }}
        }})();
        </script>
        """,
        height=1,
    )


def render_progress_tracker_board():
    """한눈에 들어오는 심플·컴팩트 실시간 학습 진도 보드."""
    scen = get_current_scenario_data()
    done_cnt, total_cnt, pct_ratio = get_scenario_progress(scen)
    flags = get_step_completion_flags()
    xp = st.session_state.get("hq_xp", 0)
    pct_int = int(pct_ratio * 100)

    def _pill(icon_label: str, is_done: bool) -> str:
        cls = "hq-step-pill done" if is_done else "hq-step-pill"
        mark = "✨ 완료" if is_done else "대기"
        return f"<div class='{cls}'>{icon_label} · {mark}</div>"

    _md_html(
        f"""
        <div class="hq-tracker-board">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">
                <div>
                    <span class="hq-badge-teal">📊 학습 진도율 {pct_int}%</span>
                    <span class="hq-badge-inter">🎯 실습 해결 {done_cnt}/{total_cnt}단계</span>
                    <span class="hq-badge-adv">⭐ {xp} XP</span>
                </div>
                <div style="font-size:0.81rem; color:#64748B; font-weight:700;">
                    단계별 미션을 완료할 때마다 진도율이 즉시 올라갑니다!
                </div>
            </div>
            <div style="background:#E0E7FF; height:11px; border-radius:999px; overflow:hidden; margin-top:0.5rem; padding:1.5px;">
                <div class="hq-progress-fill" style="width:{max(5, pct_int)}%;"></div>
            </div>
            <div class="hq-tracker-grid">
                {_pill("💬 ① 개념 질문", flags["q_done"])}
                {_pill("🌱 ② 기초 실습", flags["m1_done"])}
                {_pill("💧 ③ 중급 실습", flags["m2_done"])}
                {_pill("🔥 ④ 심화 실습", flags["m3_done"])}
                {_pill("🏆 ⑤ 협력·제출", flags["team_done"] and flags["teacher_done"])}
            </div>
        </div>
        """
    )


def render_simple_guide(step_tag: str, now_do: str):
    """글자 수를 대폭 줄여 핵심 할 일만 한 줄로 깔끔하게 안내하는 가이드 바."""
    _md_html(
        f"""
        <div class="hq-guide-bar">
            <span class="hq-badge-inter">{step_tag}</span>
            <strong style="color:#0F172A; font-size:0.95rem;">{now_do}</strong>
        </div>
        """
    )


def render_one_time_notifications():
    badge = st.session_state.pop("hq_pending_badge_notice", None)
    if badge:
        st.success(f"🏅 [배지 획득!] {badge['title']} — {badge['desc']}")

    celeb = st.session_state.pop("hq_pending_celebration", None)
    if celeb:
        if not st.session_state.get("hq_reduce_motion", False):
            st.balloons()
        st.info("🎉 기초 · 중급 · 심화 3단계 모의실습 완주 성공! 이제 [STEP 03 · 팀 협력 & 교사 피드백]으로 이동해 보세요.")


# ==============================================================================
# STEP 01: 단원 질문(2~3개) & AI 피드백 → 균형 잡힌 3열 모의실습 카드 제시
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
            "이 단원의 핵심 의학용어는 실제 간호에서 어떻게 쓰이나요?",
            "응급 보고가 필요한 기준은 무엇인가요?",
            "예비 의료인이 꼭 지켜야 할 안전 수칙은 무엇인가요?",
        ],
    )

    render_simple_guide(
        step_tag="💬 STEP 01",
        now_do="핵심 의학용어를 짚어보고 궁금한 질문 2~3개를 등록해 맞춤형 모의실습(기초·중급·심화)을 시작하세요!",
    )

    # 1) 단원 핵심 의학용어 (클릭형 캡슐 버튼)
    st.markdown("#### 💡 1. 핵심 의학용어 톡톡 카드")
    term_items = list(unit.get("key_terms", {}).items())
    if term_items:
        t_cols = st.columns(len(term_items), gap="small")
        cur_t_idx = min(st.session_state.get("hq_selected_term_idx", 0), len(term_items) - 1)
        for i, (t_name, _) in enumerate(term_items):
            short_name = t_name.split("(")[0].strip()
            with t_cols[i]:
                if st.button(
                    f"🏷️ {short_name}",
                    key=f"term_btn_{i}",
                    type="primary" if i == cur_t_idx else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["hq_selected_term_idx"] = i
                    st.session_state["hq_pending_sound"] = "pop"
                    st.rerun()

        sel_t_name, sel_t_desc = term_items[cur_t_idx]
        _md_html(
            f"""
            <div class="hq-card-blue" style="margin-top:0.2rem;">
                <span class="hq-badge-inter">용어 쏙쏙 해설</span>
                <strong style="font-size:1rem; color:#1E1B4B;">{html.escape(sel_t_name)}</strong>
                <div style="font-size:0.92rem; color:#1E293B; margin-top:0.25rem;">{html.escape(sel_t_desc)}</div>
            </div>
            """
        )

    # 2) 학생 질문 2~3개 입력 폼 (간결화)
    c_hdr, c_auto = st.columns([1.8, 1])
    with c_hdr:
        st.markdown("#### 🙋‍♀️ 2. 나의 궁금한 질문 2~3개 적기")
    with c_auto:
        if st.button("🪄 추천 질문 3개 자동 입력", type="secondary", use_container_width=True):
            st.session_state[f"q1_{unit['unit_id']}"] = sample_qs[0] if len(sample_qs) > 0 else ""
            st.session_state[f"q2_{unit['unit_id']}"] = sample_qs[1] if len(sample_qs) > 1 else ""
            st.session_state[f"q3_{unit['unit_id']}"] = sample_qs[2] if len(sample_qs) > 2 else ""
            st.session_state["hq_pending_sound"] = "chime"
            st.rerun()

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
        c_lv1, c_lv2 = st.columns([1, 1.5])
        with c_lv1:
            level_choice = st.selectbox(
                "나의 학습 난이도 선택",
                [
                    "🌱 기초부터 차근차근",
                    "💧 표준 (기초→중급→심화)",
                    "🔥 심화 (응급·우선순위 중심)",
                ],
                index=1,
            )
        with c_lv2:
            custom_sub = st.text_input(
                "세부 학습 주제 (선택 입력)",
                value=st.session_state.get("hq_custom_unit_topic", ""),
                placeholder=f"예: {unit_name}",
            )

        q1_in = st.text_input("💬 질문 1 (개념·의학용어 질문)", value=default_q1)
        q2_in = st.text_input("💬 질문 2 (병원 실습 판단 질문)", value=default_q2)
        q3_in = st.text_input("💬 질문 3 (추가로 궁금한 점 - 선택)", value=default_q3)

        submit_q_btn = st.form_submit_button(
            "✨ 질문 등록 & AI 튜터 피드백 받기",
            type="primary",
            use_container_width=True,
        )

    if submit_q_btn:
        st.session_state[f"q1_{unit['unit_id']}"] = q1_in
        st.session_state[f"q2_{unit['unit_id']}"] = q2_in
        st.session_state[f"q3_{unit['unit_id']}"] = q3_in
        st.session_state["hq_student_level"] = level_choice
        st.session_state["hq_custom_unit_topic"] = custom_sub.strip()
        entries = submit_student_questions_and_get_feedback(unit, [q1_in, q2_in, q3_in], level_choice, custom_sub)
        if entries:
            st.toast("🎶 질문 피드백과 수준별 모의실습 3단계가 준비되었습니다!")
            st.rerun()
        else:
            st.warning("질문을 1개 이상 입력해 주세요.")

    # 3) AI 보건튜터 질문 피드백
    updated_qs = get_unit_questions_for_current()
    if updated_qs:
        st.markdown("#### 🤖 3. AI 보건튜터의 질문 쏙쏙 피드백")
        for item in updated_qs:
            _md_html(
                f"""
                <div class="hq-card-selected">
                    <span class="hq-badge-teal">Q{item['q_num']}</span>
                    <strong style="font-size:0.96rem;">{html.escape(item['question'])}</strong>
                </div>
                """
            )
            st.markdown(item["feedback_markdown"])

    _md_html("<hr style='margin: 1.2rem 0; border-color: #E0E7FF;'>")

    # 4) 높이·크기가 완벽히 균형 잡힌 3열 모의실습 카드 (기초 · 중급 · 심화)
    st.markdown("#### 🎯 4. 수준별 맞춤형 모의실습 3단계 (기초 · 중급 · 심화)")

    m_cols = st.columns(3, gap="medium")
    badge_classes = ["hq-badge-basic", "hq-badge-inter", "hq-badge-adv"]
    level_tags = ["🌱 기초 미션", "💧 중급 미션", "🔥 심화 미션"]
    subs = st.session_state.get("hq_submissions", {})

    for idx, m in enumerate(missions):
        is_done = m["id"] in subs
        b_cls = badge_classes[min(idx, 2)]
        lv_tag = level_tags[min(idx, 2)]
        theme_cls = "hq-theme-done" if is_done else f"hq-theme-{min(idx, 2)}"
        status_txt = "✨ 해결 완료" if is_done else "도전 대기"
        clean_title = _clean_mission_title(m.get("title", ""))

        with m_cols[idx]:
            _md_html(
                f"""
                <div class="hq-equal-card {theme_cls}">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="{b_cls}">{lv_tag}</span>
                            <span class="hq-badge-navy">{status_txt}</span>
                        </div>
                        <div class="hq-eq-title">{html.escape(clean_title)}</div>
                        <p class="hq-eq-desc">{html.escape(m['situation'])}</p>
                    </div>
                    <div class="hq-eq-goal">
                        🎯 <strong>목표</strong> · {html.escape(m['learning_objective'])}
                    </div>
                </div>
                """
            )
            btn_lbl = f"{lv_tag} 시작하기 →" if not is_done else f"✔ {lv_tag} 결과 보기"
            if st.button(btn_lbl, key=f"go_mission_{idx}", type="primary" if not is_done else "secondary", use_container_width=True):
                st.session_state["hq_active_mission_idx"] = idx
                st.session_state["hq_nav_view"] = "STEP 02 · 기초·중급·심화 실습"
                st.session_state["hq_pending_sound"] = "chime"
                st.rerun()


# ==============================================================================
# STEP 02: 기초 · 중급 · 심화 모의실습 PBL 자기주도 해결
# ==============================================================================
def render_mission_runner():
    scenario = get_current_scenario_data()
    missions = scenario.get("missions", [])
    active_idx = min(st.session_state.get("hq_active_mission_idx", 0), len(missions) - 1)
    mission = missions[active_idx]
    m_id = mission["id"]
    level_tags = ["🌱 기초 모의실습", "💧 중급 모의실습", "🔥 심화 모의실습"]
    level_label = level_tags[min(active_idx, 2)]
    clean_title = _clean_mission_title(mission.get("title", ""))

    existing_sub = st.session_state.get("hq_submissions", {}).get(m_id)

    render_simple_guide(
        step_tag=f"🩺 STEP 02 · {level_label}",
        now_do="환자 상황과 단서를 확인하고 알맞은 판단 선택지와 개인 근거를 작성해 AI 튜터 피드백을 받으세요!",
    )

    # 기초 -> 중급 -> 심화 상단 선택 버튼
    m_cols = st.columns(len(missions), gap="small")
    for i, m_item in enumerate(missions):
        sub_i = st.session_state.get("hq_submissions", {}).get(m_item["id"])
        done_mark = " ✨완료" if sub_i else ""
        with m_cols[i]:
            if st.button(
                f"{level_tags[min(i, 2)]}{done_mark}",
                key=f"step_m_{m_item['id']}",
                type="primary" if i == active_idx else "secondary",
                use_container_width=True,
            ):
                st.session_state["hq_active_mission_idx"] = i
                st.session_state["hq_pending_sound"] = "pop"
                st.rerun()

    # [제시문 카드]
    clues_html = " &nbsp;·&nbsp; ".join([f"<strong>{html.escape(c)}</strong>" for c in mission.get("clinical_clues", [])])
    badge_cls = "hq-badge-basic" if active_idx == 0 else ("hq-badge-inter" if active_idx == 1 else "hq-badge-adv")

    _md_html(
        f"""
        <div class="hq-card" style="margin-top:0.35rem;">
            <div style="margin-bottom:0.4rem;">
                <span class="{badge_cls}">{level_label} ({active_idx + 1}/{len(missions)})</span>
                <span class="hq-badge-navy">🎯 {html.escape(mission.get('learning_objective', ''))}</span>
            </div>
            <h3 style="margin:0.15rem 0 0.65rem 0; font-size:1.22rem;">{html.escape(clean_title)}</h3>
            <div style="font-size:0.95rem; background:#F8FAFC; padding:0.95rem 1.2rem; border-radius:14px; border:1.5px solid #E2E8F0; margin-bottom:0.65rem;">
                <strong style="color:#312E81;">🏥 환자 상황</strong><br>
                <span style="color:#1E293B;">{html.escape(mission['situation'])}</span>
            </div>
            <div style="font-size:0.9rem; background:#F0FDFA; padding:0.7rem 1.1rem; border-radius:12px; border:1.5px solid #99F6E4; color:#0F766E;">
                <strong>🔎 핵심 단서</strong> &nbsp;|&nbsp; {clues_html}
            </div>
        </div>
        """
    )

    c_hint1, c_hint2 = st.columns([1.4, 1])
    with c_hint1:
        with st.expander("💡 생각 힌트 보기"):
            st.info(mission.get("hint", ""))
    with c_hint2:
        if st.button("🪄 서술 예시 문장틀 채우기", key=f"fill_rat_{m_id}", type="secondary", use_container_width=True):
            sample_rat = (
                f"환자에게서 '{mission['clinical_clues'][0]}' 단서가 관찰되므로, "
                f"환자 안전과 합병증 예방을 위해 '{mission['options'][mission['correct_index']][:38]}...' 행동을 최우선으로 수행해야 합니다."
            )
            st.session_state[f"rat_{m_id}"] = sample_rat
            st.session_state["hq_pending_sound"] = "chime"
            st.rerun()

    default_idx = existing_sub["selected_idx"] if existing_sub else 0
    default_rationale = st.session_state.get(f"rat_{m_id}", existing_sub["rationale"] if existing_sub else "")

    with st.form(key=f"form_{m_id}", clear_on_submit=False):
        st.markdown(f"#### Q. {mission['question']}")
        selected_option = st.radio(
            "1) 가장 알맞은 간호 행동 고르기",
            options=list(range(len(mission["options"]))),
            format_func=lambda idx: f"{idx + 1}번. {mission['options'][idx]}",
            index=default_idx,
            key=f"radio_{m_id}",
        )
        rationale_input = st.text_area(
            "2) 나의 PBL 판단 근거 한 줄 서술하기",
            value=default_rationale,
            height=85,
            placeholder=mission.get("pbl_writing_guide", "관찰 단서와 선택한 이유를 한 문장으로 적어보세요."),
        )
        btn_txt = "🔄 다시 제출하고 피드백 받기" if existing_sub else "✅ 개인 해결안 제출 & AI 튜터 피드백 받기"
        submitted = st.form_submit_button(btn_txt, type="primary", use_container_width=True)

    if submitted:
        st.session_state[f"rat_{m_id}"] = rationale_input
        evaluate_mission_submission(mission, selected_option, rationale_input)
        st.toast(f"🎵 {level_label} 제출 완료! AI 피드백이 도착했습니다.")
        st.rerun()

    sub = st.session_state.get("hq_submissions", {}).get(m_id)
    if sub:
        if sub.get("is_correct"):
            _md_html(
                f"""
                <div class="hq-card-selected">
                    <span class="hq-badge-teal">✨ 정답 & 개인 서술 완료</span>
                    <span class="hq-badge-navy">{html.escape(sub.get('rationale_status', ''))}</span>
                    <div style="font-size:0.92rem; margin-top:0.45rem;">
                        <strong>✍️ 나의 서술</strong>: "{html.escape(sub.get('rationale') or '(서술 미입력)')}"
                    </div>
                </div>
                """
            )
        else:
            _md_html(
                f"""
                <div class="hq-card-coral">
                    <span class="hq-badge-coral">💪 재도전 코칭 (감점 없음)</span>
                    <div style="font-size:0.92rem; margin-top:0.35rem;">
                        아래 AI 튜터의 힌트를 읽고 다시 선택해 보세요!
                    </div>
                </div>
                """
            )

        st.info(sub.get("ai_individual_feedback", ""))

        with st.expander("📖 1~4번 선택지별 상세 해설 보기"):
            for idx, exp_text in enumerate(mission.get("option_explanations", [])):
                prefix = "✔ [정답] " if idx == mission.get("correct_index") else f"• [{idx + 1}번] "
                st.markdown(f"**{prefix}{mission['options'][idx]}**\n  - {exp_text}")

        if active_idx < len(missions) - 1:
            next_lv = level_tags[min(active_idx + 1, 2)]
            if st.button(f"👉 다음 미션 [{next_lv}] 도전하기 →", type="primary", use_container_width=True):
                st.session_state["hq_active_mission_idx"] = active_idx + 1
                st.session_state["hq_pending_sound"] = "chime"
                st.rerun()
        else:
            if st.button("🏆 3단계 모두 완료! [STEP 03 · 팀 협력 & 교사 피드백]으로 이동 →", type="primary", use_container_width=True):
                st.session_state["hq_nav_view"] = "STEP 03 · 팀 협력 & 교사 피드백"
                st.session_state["hq_pending_sound"] = "fanfare"
                st.rerun()


# ==============================================================================
# STEP 03: 팀별 협력 제출 → AI 팀 피드백 → 교사 피드백 & 제출함·인쇄
# ==============================================================================
def _build_printable_activity_sheet_html() -> str:
    """인쇄 및 파일 제출용 디지털 학습지 HTML."""
    unit_name = st.session_state.get("hq_selected_unit", "")
    scenario = get_current_scenario_data()
    completed, total, pct = get_scenario_progress(scenario)
    xp = st.session_state.get("hq_xp", 0)
    student_name = st.session_state.get("hq_student_label", "")
    group_name = st.session_state.get("hq_group_label", "")
    notes = st.session_state.get("hq_team_notes", {})
    qs = get_unit_questions_for_current()

    q_rows = "".join([f"<li><strong>Q{q['q_num']}</strong>: {html.escape(q['question'])}</li>" for q in qs]) or "<li>(작성된 질문 없음)</li>"

    m_rows = ""
    for m in scenario.get("missions", []):
        sub = st.session_state.get("hq_submissions", {}).get(m["id"])
        lv = m.get("level_label", f"미션 {m.get('step_num', 1)}")
        if sub:
            choice_str = f"{sub['selected_idx'] + 1}번. {html.escape(sub['selected_text'])}"
            rat_str = html.escape(sub.get("rationale") or "-")
            fb_short = html.escape(sub.get("rationale_status") or "완료")
        else:
            choice_str, rat_str, fb_short = "(미제출)", "-", "미제출"

        m_rows += f"""
        <tr>
            <td style="font-weight:700; text-align:center;">{html.escape(lv)}</td>
            <td><strong>{html.escape(_clean_mission_title(m['title']))}</strong><br><span style="font-size:12px; color:#475569;">선택: {choice_str}</span></td>
            <td>{rat_str}</td>
            <td style="font-size:12px; color:#0F766E;">{fb_short}</td>
        </tr>
        """

    ai_team_fb_clean = html.escape(notes.get("ai_team_feedback") or "(팀 협력 제출 후 표시됩니다)").replace("\n", "<br>")
    teacher_fb_clean = html.escape(notes.get("teacher_feedback") or "(교사 피드백 요청 후 표시됩니다)").replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>보건간호 디지털 PBL 학습지</title>
<style>
    @font-face {{
        font-family: 'NanumSquareRound';
        src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_two@1.0/NanumSquareRound.woff') format('woff');
    }}
    body {{
        font-family: 'NanumSquareRound', 'Malgun Gothic', sans-serif;
        color: #1E293B; background: #F8FAFC; margin: 14px; line-height: 1.55; word-break: keep-all;
    }}
    .sheet {{
        max-width: 840px; margin: 0 auto; background: #FFFFFF; border: 2px solid #C7D2FE;
        border-top: 6px solid #6366F1; border-radius: 16px; padding: 22px 26px;
    }}
    .top-bar {{
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 2px solid #E0E7FF; padding-bottom: 10px; margin-bottom: 12px;
    }}
    h1 {{ margin: 0; font-size: 19px; color: #1E1B4B; }}
    h2 {{ font-size: 14px; color: #4338CA; margin: 14px 0 6px 0; padding-left: 8px; border-left: 4px solid #6366F1; }}
    .meta {{
        display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px;
        background: #EEF2FF; border-radius: 10px; padding: 10px 14px; font-size: 13px; margin-bottom: 12px;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
    th, td {{ border: 1px solid #CBD5E1; padding: 7px 9px; text-align: left; vertical-align: top; }}
    th {{ background: #EEF2FF; color: #312E81; }}
    .box {{ background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 10px; padding: 9px 13px; font-size: 12.5px; }}
    .teacher-box {{ background: #FFFBEB; border: 1.5px solid #FCD34D; border-radius: 10px; padding: 9px 13px; font-size: 12.5px; }}
    .print-btn {{
        background: linear-gradient(135deg, #6366F1, #3B82F6); color: #FFFFFF; border: none;
        border-radius: 10px; padding: 7px 14px; font-size: 13px; font-weight: 700; cursor: pointer;
    }}
    @media print {{ .no-print {{ display: none !important; }} body {{ margin: 0; background: #FFFFFF; }} }}
</style>
</head>
<body>
<div class="sheet">
    <div class="top-bar">
        <div>
            <h1>🩺 {html.escape(SITE_CONFIG['site_title'])} — 디지털 학습 결과지</h1>
        </div>
        <div class="no-print">
            <button class="print-btn" onclick="window.print()">🖨️ 인쇄 / PDF 저장</button>
        </div>
    </div>
    <div class="meta">
        <div><strong>학번 / 이름</strong>: {html.escape(student_name or '미입력')}</div>
        <div><strong>모둠명</strong>: {html.escape(group_name or '미입력')}</div>
        <div><strong>학습 단원</strong>: {html.escape(unit_name)}</div>
        <div><strong>달성 진도율</strong>: {int(pct * 100)}% ({completed}/{total}단계 · {xp} XP)</div>
    </div>
    <h2>1. 나의 단원 질문 (2~3개)</h2>
    <div class="box"><ul style="margin:0; padding-left:18px;">{q_rows}</ul></div>
    <h2>2. 기초 · 중급 · 심화 개인별 PBL 해결 기록</h2>
    <table>
        <thead>
            <tr><th style="width:14%;">단계</th><th style="width:32%;">상황 및 선택</th><th style="width:34%;">개인 PBL 근거 서술</th><th style="width:20%;">AI 튜터 확인</th></tr>
        </thead>
        <tbody>{m_rows}</tbody>
    </table>
    <h2>3. 팀 협력 해결안 및 AI 튜터 팀 피드백</h2>
    <div class="box">
        <div><strong>• 팀원 의견 비교</strong>: {html.escape(notes.get('peer_comparison') or '-')}</div>
        <div><strong>• 팀 최종 해결안</strong>: {html.escape(notes.get('team_conclusion') or '-')}</div>
        <div><strong>• 협력 성찰</strong>: {html.escape(notes.get('thought_change') or '-')}</div>
        <hr style="border:none; border-top:1px dashed #CBD5E1; margin:7px 0;">
        <div style="color:#0F766E;">{ai_team_fb_clean}</div>
    </div>
    <h2>4. 담당 교사 최종 피드백</h2>
    <div class="teacher-box"><strong>👩‍🏫 교사 종합 피드백</strong><br>{teacher_fb_clean}</div>
</div>
</body>
</html>"""


def render_collaboration_and_growth():
    scenario = get_current_scenario_data()
    missions = scenario.get("missions", [])
    subs = st.session_state.get("hq_submissions", {})
    notes = st.session_state.get("hq_team_notes", {})

    render_simple_guide(
        step_tag="🏆 STEP 03",
        now_do="팀 협력 해결안을 작성해 AI 팀 피드백과 교사 최종 피드백을 받고 선생님께 보고서를 제출하세요!",
    )

    auto_ind_lines = []
    for m in missions:
        s = subs.get(m["id"])
        lv = m.get("level_label", f"단계 {m.get('step_num', 1)}")
        if s and s.get("rationale"):
            auto_ind_lines.append(f"[{lv}] {s['rationale']}")
        elif s:
            auto_ind_lines.append(f"[{lv}] {s['selected_idx']+1}번 선택 완료")
    auto_ind_summary = " / ".join(auto_ind_lines) if auto_ind_lines else "환자 안전과 관찰·보고 원칙에 따라 기초·중급·심화 간호 우선순위를 판단함."

    c_hdr, c_fill = st.columns([1.8, 1])
    with c_hdr:
        st.markdown("#### 🤝 1. 개인 서술 종합 & 팀 협력 해결안 작성")
    with c_fill:
        if st.button("🪄 팀 협력 예시 자동 채우기", type="secondary", use_container_width=True):
            st.session_state["hq_team_notes"]["individual_summary"] = auto_ind_summary
            st.session_state["hq_team_notes"]["peer_comparison"] = "나는 개별 처치 절차에 집중했는데, 팀원들은 주변 환자 분리와 환경 안전 단서까지 함께 짚어주었다."
            st.session_state["hq_team_notes"]["team_conclusion"] = "1순위: 보호구 착용 및 안전 확보 → 2순위: 활력징후·증상 사정 후 즉시 보고 → 3순위: 비침습적 안정 간호 시행"
            st.session_state["hq_team_notes"]["thought_change"] = "팀원들과 임상 단서를 비교하며 더 안전한 간호 우선순위를 세울 수 있었고 업무 경계를 명확히 이해했다."
            st.session_state["hq_pending_sound"] = "chime"
            st.rerun()

    with st.form("team_collab_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            s_name_in = st.text_input("👤 학번 및 이름", value=st.session_state.get("hq_student_label", ""), placeholder="예: 2학년 1반 홍길동")
        with c2:
            g_name_in = st.text_input("👥 모둠 이름", value=st.session_state.get("hq_group_label", ""), placeholder="예: 나이팅게일 1모둠")

        ind_sum_in = st.text_area("① 개인별 해결 내용 요약 (자동 연동)", value=notes.get("individual_summary") or auto_ind_summary, height=62)
        peer_comp_in = st.text_input("② 팀원과 생각 비교 (같거나 달랐던 점)", value=notes.get("peer_comparison", ""))
        team_conc_in = st.text_area("③ 우리 팀 최종 해결안 및 우선순위 근거", value=notes.get("team_conclusion", ""), height=68)
        thought_chg_in = st.text_input("④ 팀 토의 후 새롭게 배운 점", value=notes.get("thought_change", ""))

        team_sub_btn = st.form_submit_button("✅ 팀 해결안 제출 & AI 튜터 팀 피드백 받기", type="primary", use_container_width=True)

    if team_sub_btn:
        submit_team_collaboration_and_get_feedback(
            student_name=s_name_in,
            group_name=g_name_in,
            individual_summary=ind_sum_in,
            peer_comparison=peer_comp_in,
            team_conclusion=team_conc_in,
            thought_change=thought_chg_in,
        )
        st.toast("🎶 AI 보건튜터 팀 피드백이 생성되었습니다!")
        st.rerun()

    updated_notes = st.session_state.get("hq_team_notes", {})
    if updated_notes.get("ai_team_feedback"):
        st.markdown("#### 🤖 2. AI 보건튜터 팀 피드백")
        st.info(updated_notes["ai_team_feedback"])

    _md_html("<hr style='margin: 1.1rem 0; border-color: #E0E7FF;'>")

    st.markdown("#### 👩‍🏫 3. 교사 최종 피드백 & 선생님께 보고서 제출")
    col_t1, col_t2 = st.columns([1.2, 1.8])
    with col_t1:
        if st.button("📤 선생님께 최종 제출 & 교사 피드백 확인", type="primary", use_container_width=True):
            entry = submit_final_report_to_teacher()
            if not st.session_state.get("hq_reduce_motion", False):
                st.balloons()
            st.toast(f"🎉 [{entry['student_name']}] 최종 보고서가 선생님 제출함에 등록되었습니다!")
            st.rerun()
    with col_t2:
        with st.expander("👩‍🏫 교사 직접 코멘트 작성 (선생님 전용)"):
            custom_t = st.text_area("교사 코멘트 입력", value=updated_notes.get("teacher_feedback", ""))
            if st.button("코멘트 저장", type="secondary"):
                generate_or_save_teacher_feedback(custom_t)
                st.rerun()

    updated_notes = st.session_state.get("hq_team_notes", {})
    if updated_notes.get("teacher_feedback"):
        _md_html(
            f"""
            <div class="hq-card-teacher">
                <span class="hq-badge-adv">✨ 교사 피드백 & 제출 완료</span>
                <div style="font-size:0.93rem; color:#1E293B; margin-top:0.35rem;">{html.escape(updated_notes['teacher_feedback'])}</div>
            </div>
            """
        )

    _md_html("<hr style='margin: 1.1rem 0; border-color: #E0E7FF;'>")

    st.markdown("#### 🖨️ 4. 학습지 저장·인쇄 & 교사용 제출물 관리함")
    sheet_html = _build_printable_activity_sheet_html()
    reports_cnt = len(load_submitted_reports())

    d_col1, d_col2 = st.columns(2, gap="medium")
    with d_col1:
        st.download_button(
            label="📥 내 디지털 학습지 파일(.html) 저장",
            data=sheet_html,
            file_name=f"보건간호_디지털학습지_{st.session_state.get('hq_student_label') or '학생'}.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )
    with d_col2:
        st.download_button(
            label=f"📊 교사용: 제출 보고서 엑셀(CSV) 다운로드 ({reports_cnt}명)",
            data=export_submitted_reports_csv(),
            file_name="HEALTH_QUEST_학생제출보고서_전체목록.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander(f"📂 교사용 제출물 통합 관리함 ({reports_cnt}건 확인)"):
        all_reps = load_submitted_reports()
        if not all_reps:
            st.caption("아직 제출된 보고서가 없습니다.")
        else:
            for idx, r in enumerate(reversed(all_reps), start=1):
                _md_html(
                    f"""
                    <div class="hq-card" style="padding:0.8rem 1.1rem; margin-bottom:0.5rem;">
                        <span class="hq-badge-teal">#{idx} {html.escape(r.get('student_name', ''))} ({html.escape(r.get('group_name', ''))})</span>
                        <span class="hq-badge-inter">{html.escape(r.get('unit_name', ''))}</span>
                        <span class="hq-badge-adv">진도율 {r.get('progress_pct', 0)}%</span>
                        <span style="font-size:0.78rem; color:#64748B; float:right;">{html.escape(r.get('submitted_at', ''))}</span>
                    </div>
                    """
                )

    with st.expander("📄 디지털 학습지 인쇄용 미리보기", expanded=True):
        components.html(sheet_html, height=600, scrolling=True)
