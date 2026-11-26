"""Teacher assessment criteria for Firebase PBL submissions."""

from collections.abc import Mapping


EVALUATION_STATUS = {
    "submitted": "제출 완료",
    "reviewing": "검토 중",
    "revision_requested": "보완 요청",
    "evaluated": "평가 완료",
}
SCORE_LEVELS = {
    25: "근거가 구체적이고 기준을 충족함",
    20: "대체로 충족하며 일부 보완이 필요함",
    15: "일부를 충족하나 중요한 근거가 빠짐",
    10: "시도는 있으나 기준 충족을 판단하기 어려움",
    0: "제출물에서 확인할 수 있는 증거가 없음",
}

# Each row contains a stable key, display name, and evidence for full credit.
RUBRICS = {
    "individual_v1": ("개인 학습자료", (
        ("concept", "개념 적용", "단원 핵심 개념을 정확히 설명하고 선택한 상황에 적용했다."),
        ("evidence", "핵심 단서와 판단 근거", "관찰된 단서를 짚고 그 단서가 자신의 판단을 어떻게 뒷받침하는지 설명했다."),
        ("safety", "안전과 우선순위", "상황에 맞는 안전 행동을 순서대로 제시하고 학생의 역할과 보고 범위를 지켰다."),
        ("reflection", "성찰과 보완", "놓쳤던 점이나 생각이 바뀐 이유를 설명하고 다음에 보완할 행동을 구체적으로 제안했다."),
    )),
    "team_material_v1": ("모둠 학습자료", (
        ("concept", "상황 이해와 수업 근거", "모둠 답안이 핵심 단서와 단원 개념을 연결한다."),
        ("safety", "안전과 우선순위", "해결안에 안전 행동의 순서와 관찰·보고 범위가 분명하다."),
        ("collaboration", "협력과 합의", "서로 다른 의견을 검토한 흔적과 최종 합의 이유가 확인된다."),
        ("communication", "자료 구성과 전달", "문제, 해결안과 근거를 다른 사람이 따라갈 수 있게 정리했다."),
    )),
    "team_simulation_v1": ("모의상황실습 · 모둠 음성 수행평가", (
        ("concept", "상황 분석과 수업 근거", "핵심 단서와 문제를 구분하고 판단을 수업에서 배운 근거로 설명했다."),
        ("safety", "환자 안전과 우선순위", "안전 행동의 순서와 역할 범위를 적절히 설명하고 관찰·보고 계획을 포함했다."),
        ("collaboration", "모둠 합의와 역할", "검토한 의견이나 대안을 짚고, 합의한 해결안과 팀원 역할을 설명했다."),
        ("communication", "음성 전달과 답안 일치", "녹음에서 공동 답안의 핵심 행동과 판단 이유를 알아들을 수 있게 설명했다."),
    )),
}


def rubric_for_submission(item: Mapping) -> str:
    if item.get("activity") == "final_simulation":
        return "team_simulation_v1"
    return "team_material_v1" if item.get("submission_type") == "팀" else "individual_v1"


def status_label(status: str) -> str:
    return EVALUATION_STATUS.get(status, status)


def validate_rubric_scores(rubric_id: str, scores: Mapping) -> dict[str, int]:
    expected = {key for key, _, _ in RUBRICS[rubric_id][1]}
    if set(scores) != expected or any(type(value) is not int or value not in SCORE_LEVELS for value in scores.values()):
        raise ValueError("모든 루브릭 항목에 점수 수준을 선택해 주세요.")
    return {key: scores[key] for key, _, _ in RUBRICS[rubric_id][1]}
