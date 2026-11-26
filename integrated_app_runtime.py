"""Shared runtime for the two HEALTH QUEST integrated deployments."""

import streamlit as st

from firebase_integration import (
    load_firebase_settings,
    persist_current_learning_state,
    require_authenticated_identity,
    restore_learning_unit,
    sign_out_student_code,
)
from quest_engine import get_current_scenario_data, init_quest_state, simulation_ready


def run_integrated_app(*, firebase_required: bool = False, student_login_mode: str | None = None) -> None:
    """Render the integrated mission-room and simulation application."""
    st.set_page_config(
        page_title="HEALTH QUEST — 통합 간호 PBL",
        page_icon=":material/clinical_notes:",
        layout="wide",
    )

    if student_login_mode:
        st.session_state["hq_fixed_student_login_mode"] = student_login_mode
    firebase_settings = load_firebase_settings()
    if firebase_required and not firebase_settings.enabled:
        st.error("Firebase 설정을 확인해 주세요. 학생 자료 보호를 위해 로그인 화면을 열 수 없습니다.")
        st.stop()
    identity = require_authenticated_identity(firebase_settings)
    if student_login_mode:
        st.session_state["hq_fixed_student_login_mode"] = student_login_mode

    st.session_state["hq_integrated_mode"] = True
    init_quest_state()

    if identity is not None:
        if identity.uses_access_code:
            st.sidebar.caption(identity.name)
            st.sidebar.button("접속코드 로그아웃", on_click=sign_out_student_code, key="hq_logout_global")
        else:
            st.sidebar.caption(f"{identity.name} · {'교사' if identity.role == 'teacher' else '학생'} · {identity.email}")
            st.sidebar.button("Google 계정 전환 / 로그아웃", on_click=st.logout, key="hq_logout_global")
        if identity.role == "student":
            restore_learning_unit(firebase_settings, identity)
        elif identity.role == "teacher":
            st.navigation([
                st.Page("teacher_dashboard.py", title="교사 대시보드", icon=":material/dashboard:", default=True),
            ], position="top").run()
            return

    pages = [
        st.Page(
            "app.py",
            title="간호 미션룸",
            icon=":material/clinical_notes:",
            default=True,
        )
    ]

    if firebase_settings.enabled or simulation_ready(get_current_scenario_data()):
        pages.append(
            st.Page(
                "app_rag_pbl.py",
                title="모의상황실습",
                icon=":material/biotech:",
            )
        )

    if firebase_settings.enabled and identity is not None and identity.role == "student":
        pages.append(
            st.Page(
                "student_submission.py",
                title="수행평가 제출",
                icon=":material/upload_file:",
                url_path="student_submission",
            )
        )

    navigation = st.navigation(pages, position="top")
    navigation.run()
    persist_current_learning_state(firebase_settings, identity)
    if st.session_state.get("hq_firebase_sync_error"):
        st.warning("Firebase에 학습기록을 저장하지 못했습니다. 화면을 유지하고 다시 저장해 주세요.")
