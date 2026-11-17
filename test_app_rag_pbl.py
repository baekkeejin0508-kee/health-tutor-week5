import os

from streamlit.testing.v1 import AppTest

from rag_pbl_single_agent import guard_student_text


def test_privacy_guard_blocks_identifiers_and_real_care_requests():
    assert not guard_student_text("연락처는 010-1234-5678입니다").safe
    assert not guard_student_text("증상에 무슨 약을 먹어야 하나요?").safe
    assert guard_student_text("표준주의와 비말주의의 차이가 궁금합니다").safe


def test_demo_learning_flow_reaches_feedback_and_excel():
    os.environ["RAG_PBL_FORCE_DEMO"] = "true"
    at = AppTest.from_file("app_rag_pbl.py", default_timeout=30).run()
    assert not at.exception

    at.text_input[0].set_value("표준주의와 격리주의는 어떤 단서로 구분하나요?")
    at.text_input[1].set_value("환자 안전을 위해 무엇을 먼저 관찰하고 보고해야 하나요?")
    at.text_area[0].set_value(
        "표준주의는 모든 환자에게 적용하고, 환자의 증상과 전파 경로를 관찰하여 추가 격리 원칙을 판단한다고 배웠습니다."
    )
    at.form_submit_button[0].click().run(timeout=30)
    assert not at.exception
    assert at.session_state["ragpbl_discovery"] is not None
    assert len(at.session_state["ragpbl_discovery"].scenarios) == 3

    at.button(key="ragpbl_select_A").click().run(timeout=30)
    assert not at.exception
    assert at.session_state["ragpbl_selected_id"] == "A"

    answers = {
        "ragpbl_problem": "환자의 상태와 감염 가능 단서를 먼저 확인하고 다른 환자에게 전파될 위험을 문제로 정의했습니다.",
        "ragpbl_hypothesis": "현재 단서가 감염 전파 위험을 높이므로 표준주의와 필요한 추가 주의를 함께 적용해야 한다고 판단했습니다.",
        "ragpbl_action_plan": "먼저 손 위생과 보호구를 확인하고 환자의 관찰 가능한 상태를 사정한 뒤 담당 간호사에게 즉시 보고하겠습니다.",
        "ragpbl_evidence": "표준주의는 모든 환자의 혈액과 체액을 감염 가능성이 있는 것으로 보고 적용한다는 수업 개념에 근거했습니다.",
        "ragpbl_evaluation": "환자의 상태 변화와 감염 노출 위험이 줄었는지 관찰하고, 보고 후 추가 지시가 수행되었는지 확인하겠습니다.",
    }
    for key, value in answers.items():
        at.text_area(key=key).set_value(value)
    at.form_submit_button[0].click().run(timeout=30)
    assert not at.exception
    assert at.session_state["ragpbl_review"] is not None
    assert at.download_button
