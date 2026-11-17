"""Run: streamlit run app_integrated.py

HEALTH QUEST — 간호 미션룸과 RAG 모의상황실습을 연결한 통합 학습 앱.
"""

import streamlit as st

from quest_engine import get_current_scenario_data, get_scenario_progress, init_quest_state


st.set_page_config(
    page_title="HEALTH QUEST — 통합 간호 PBL",
    page_icon=":material/clinical_notes:",
    layout="wide",
)

st.session_state["hq_integrated_mode"] = True
init_quest_state()

scenario = get_current_scenario_data()
completed, total, _ = get_scenario_progress(scenario)
simulation_unlocked = total > 0 and completed == total

pages = [
    st.Page(
        "app.py",
        title="간호 미션룸",
        icon=":material/clinical_notes:",
        default=True,
    )
]

if simulation_unlocked:
    pages.append(
        st.Page(
            "app_rag_pbl.py",
            title="모의상황실습",
            icon=":material/biotech:",
        )
    )

navigation = st.navigation(pages, position="top")
navigation.run()
