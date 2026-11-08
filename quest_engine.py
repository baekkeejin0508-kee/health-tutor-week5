"""HEALTH QUEST — 스마트 디지털 보건간호 PBL 학습지: 상태 관리·진도율 계산·AI 보건튜터(질문/개인/팀) 및 교사 피드백 엔진."""
from datetime import datetime, timezone
import streamlit as st
from quest_data import UNIT_CATALOG

BADGE_DEFINITIONS = {
    "question_explorer": {
        "id": "question_explorer",
        "title": "자기주도 질문 탐구자",
        "desc": "단원의 모르는 개념과 의학용어 질문을 2~3개 작성하고 AI 보건튜터 피드백으로 맞춤형 실습을 설계했습니다.",
        "competency": "자기주도 탐구 역량",
    },
    "first_mission": {
        "id": "first_mission",
        "title": "기초 모의실습 해결",
        "desc": "기초 모의실습 상황에서 핵심 단서를 파악하고 첫 임상 판단 및 개인 서술을 완료했습니다.",
        "competency": "기초 임상추론 역량",
    },
    "evidence_thinker": {
        "id": "evidence_thinker",
        "title": "중급 PBL 우선순위 추론가",
        "desc": "중급 모의실습에서 환자안전과 법적 업무 경계를 고려해 우선순위 근거를 논리적으로 서술했습니다.",
        "competency": "문제해결 역량",
    },
    "pbl_master": {
        "id": "pbl_master",
        "title": "기초·중급·심화 완전학습 달성",
        "desc": "기초·중급·심화 3단계 모의실습을 모두 자기주도적으로 서술·해결하고 AI 개인 피드백을 확인했습니다.",
        "competency": "현장 실무 통합 역량",
    },
    "team_collaborator": {
        "id": "team_collaborator",
        "title": "팀 협력 & 최종 성찰 완수",
        "desc": "팀별 협력 해결안을 도출하여 AI 보건튜터 팀 피드백과 교사 최종 피드백까지 완수했습니다.",
        "competency": "보건의료 협업 역량",
    },
}


def init_quest_state():
    """세션 상태 초기화 (KeyError 방지를 위해 모든 상태 키를 기본값으로 보장)."""
    first_unit_key = list(UNIT_CATALOG.keys())[0]
    first_scen_id = UNIT_CATALOG[first_unit_key]["scenarios"][0]["scenario_id"]
    defaults = {
        "hq_site_title": "HEALTH QUEST — 예비 보건의료인의 미션룸",
        "hq_nav_view": "STEP 01 · 단원 질문 & 피드백",
        "hq_selected_unit": first_unit_key,
        "hq_custom_unit_topic": "",
        "hq_student_level": "표준 (기초→중급→심화 순차 도전)",
        "hq_selected_scenario_id": first_scen_id,
        "hq_active_mission_idx": 0,  # 0: 기초, 1: 중급, 2: 심화
        "hq_reduce_motion": False,
        "hq_selected_term_idx": 0,
        # 1단계: 학생 질문 2~3개 및 AI 피드백, 모의실습 3단계 생성 여부
        "hq_unit_questions": [],  # unit별 질문·피드백 리스트
        "hq_scenarios_generated": {},  # unit_name -> bool (질문 기반 모의실습 3개 제시 완료 여부)
        # 2~3단계: 기초·중급·심화 개인별 제출 및 AI 개인 피드백
        "hq_submissions": {},  # mission_id -> submission dict (ai_individual_feedback 포함)
        "hq_reflections": {},  # mission_id -> str
        # 4단계: 팀별 협력 서술, AI 팀 피드백, 교사 최종 피드백
        "hq_student_label": "",
        "hq_group_label": "",
        "hq_team_notes": {
            "individual_summary": "",
            "peer_comparison": "",
            "team_conclusion": "",
            "thought_change": "",
            "ai_team_feedback": "",
            "teacher_feedback": "",
            "saved_at": "",
        },
        # 보상 및 진도 기록
        "hq_rewarded_keys": [],
        "hq_earned_badges": [],
        "hq_xp": 0,
        "hq_growth_log": [],
        "hq_pending_badge_notice": None,
        "hq_pending_celebration": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_current_unit_data() -> dict:
    unit_name = st.session_state.get("hq_selected_unit")
    if unit_name not in UNIT_CATALOG:
        unit_name = list(UNIT_CATALOG.keys())[0]
        st.session_state["hq_selected_unit"] = unit_name
    return UNIT_CATALOG[unit_name]


def get_current_scenario_data() -> dict:
    unit = get_current_unit_data()
    scen_id = st.session_state.get("hq_selected_scenario_id", "")
    for scen in unit["scenarios"]:
        if scen["scenario_id"] == scen_id:
            return scen
    first_scen = unit["scenarios"][0]
    st.session_state["hq_selected_scenario_id"] = first_scen["scenario_id"]
    return first_scen


def get_unit_questions_for_current() -> list[dict]:
    unit_name = st.session_state.get("hq_selected_unit", "")
    all_qs = st.session_state.get("hq_unit_questions", [])
    return [q for q in all_qs if q.get("unit_name") == unit_name]


def get_scenario_progress(scenario: dict) -> tuple[int, int, float]:
    """
    기초·중급·심화 3단계 모의실습 완료 개수 및 전체 학습 진도율(0.0~1.0) 반환.
    - 학생이 미션을 제출하는 즉시 완료 개수와 진도율이 반영되도록 개선.
    """
    missions = scenario.get("missions", [])
    total = len(missions)
    completed_missions = 0
    correct_missions = 0

    for m in missions:
        sub = st.session_state.get("hq_submissions", {}).get(m["id"])
        if sub is not None:
            completed_missions += 1
            if sub.get("is_correct"):
                correct_missions += 1

    # 전체 5단계 가중 진도율 계산 (질문 20% + 실습생성 10% + 기초/중급/심화 55% + 팀/교사피드백 15%)
    unit_name = st.session_state.get("hq_selected_unit", "")
    has_questions = len(get_unit_questions_for_current()) >= 1
    has_generated = bool(st.session_state.get("hq_scenarios_generated", {}).get(unit_name))
    team_notes = st.session_state.get("hq_team_notes", {})
    has_team = bool(team_notes.get("ai_team_feedback"))
    has_teacher = bool(team_notes.get("teacher_feedback"))

    pct = 0.0
    if has_questions:
        pct += 0.20
    if has_generated:
        pct += 0.10
    if total > 0:
        # 미션 제출 시 개당 12%, 정답+서술 시 추가 6.3% (3개 합산 약 55%)
        pct += (completed_missions / total) * 0.35 + (correct_missions / total) * 0.20
    if has_team:
        pct += 0.08
    if has_teacher:
        pct += 0.07

    pct = min(1.0, round(pct, 2))
    # 만약 3개 미션을 모두 제출했다면 최소 75% 이상 표시 보장
    if completed_missions == total and total > 0 and pct < 0.75:
        pct = 0.75
    if completed_missions == total and has_team and has_teacher:
        pct = 1.0

    return completed_missions, total, pct


def get_step_completion_flags() -> dict:
    """상단 진도 트래커에 표시할 단계별 완료 상태 반환."""
    unit_name = st.session_state.get("hq_selected_unit", "")
    scen = get_current_scenario_data()
    missions = scen.get("missions", [])
    subs = st.session_state.get("hq_submissions", {})
    team_notes = st.session_state.get("hq_team_notes", {})

    q_done = len(get_unit_questions_for_current()) >= 1
    scen_ready = bool(st.session_state.get("hq_scenarios_generated", {}).get(unit_name)) or q_done
    m1_done = bool(missions and subs.get(missions[0]["id"]))
    m2_done = bool(len(missions) > 1 and subs.get(missions[1]["id"]))
    m3_done = bool(len(missions) > 2 and subs.get(missions[2]["id"]))
    team_done = bool(team_notes.get("ai_team_feedback"))
    teacher_done = bool(team_notes.get("teacher_feedback"))

    return {
        "q_done": q_done,
        "scen_ready": scen_ready,
        "m1_done": m1_done,
        "m2_done": m2_done,
        "m3_done": m3_done,
        "team_done": team_done,
        "teacher_done": teacher_done,
    }


def award_action_once(action_key: str, action_type: str, label: str, xp_gain: int, badge_id: str | None = None) -> bool:
    if action_key in st.session_state["hq_rewarded_keys"]:
        return False

    st.session_state["hq_rewarded_keys"].append(action_key)
    st.session_state["hq_xp"] = st.session_state.get("hq_xp", 0) + xp_gain
    st.session_state["hq_growth_log"].append(
        {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "action_type": action_type,
            "label": label,
            "xp_gain": xp_gain,
        }
    )

    if badge_id and badge_id in BADGE_DEFINITIONS and badge_id not in st.session_state["hq_earned_badges"]:
        st.session_state["hq_earned_badges"].append(badge_id)
        st.session_state["hq_pending_badge_notice"] = BADGE_DEFINITIONS[badge_id]

    return True


def _build_single_question_feedback(unit_data: dict, q_text: str, student_level: str) -> str:
    """단원 핵심 용어 사전 및 임상 원칙을 기반으로 학생 질문에 대한 맞춤형 AI 보건튜터 답변 생성."""
    clean_q = q_text.strip()
    matched_term = None
    matched_desc = None
    for term_name, desc in unit_data.get("key_terms", {}).items():
        core_word = term_name.split("(")[0].strip()
        if core_word in clean_q or any(tok in clean_q for tok in core_word.split("·") if len(tok) >= 2):
            matched_term = term_name
            matched_desc = desc
            break

    safety_keywords = ["직접 주사", "내가 처방", "약 먹", "락스", "혼합", "도뇨관 삽입", "절개", "가위로"]
    has_safety_concern = any(k in clean_q for k in safety_keywords)

    if matched_term:
        explanation = f"**핵심 개념 풀이 ({matched_term})**: {matched_desc}"
    else:
        first_term, first_desc = list(unit_data.get("key_terms", {}).items())[0]
        explanation = (
            f"**단원 핵심 원리 연결**: 질문하신 내용은 **{unit_data.get('subject', '보건간호')}** 교과서의 "
            f"환자 사정 및 안전 간호 원칙과 직결됩니다. 특히 **{first_term}**({first_desc})을 함께 기억하면 임상 판단이 훨씬 명확해집니다."
        )

    safety_note = ""
    if has_safety_concern:
        safety_note = (
            "\n- **[Safety Reviewer 안전 경계 안내]**: 침습적 처치(도뇨·주사·절개), 임의 약물 투여, 소독제 혼합은 "
            "환자 안전과 법적 업무 범위에 위배되므로 절대 직접 시행하지 않고 **활력징후·증상 관찰 후 담당 간호사·의사에게 즉시 보고**해야 합니다."
        )

    return (
        f"- {explanation}\n"
        f"- **PBL 실습 연결 팁 ({student_level})**: 이 질문의 핵심 단서를 아래 **[기초 → 중급 → 심화 모의실습]** 상황에서 찾아 직접 적용해 보세요.{safety_note}"
    )


def submit_student_questions_and_get_feedback(
    unit_data: dict,
    questions: list[str],
    student_level: str,
    custom_topic: str = "",
) -> list[dict]:
    """학생이 작성한 2~3개의 질문을 받아 각각 AI 보건튜터 피드백을 생성하고, 수준별 모의실습 3단계(기초·중급·심화)를 활성화."""
    unit_name = st.session_state.get("hq_selected_unit", "")
    valid_qs = [q.strip() for q in questions if q and q.strip()]
    if not valid_qs:
        return []

    # 기존 다른 단원 질문은 유지하고 현재 단원 질문은 최신 입력으로 갱신
    other_unit_qs = [item for item in st.session_state.get("hq_unit_questions", []) if item.get("unit_name") != unit_name]
    new_entries = []
    for idx, q_str in enumerate(valid_qs, start=1):
        fb_md = _build_single_question_feedback(unit_data, q_str, student_level)
        entry = {
            "unit_name": unit_name,
            "q_num": idx,
            "question": q_str,
            "level": student_level,
            "custom_topic": custom_topic.strip(),
            "feedback_markdown": fb_md,
        }
        new_entries.append(entry)

    st.session_state["hq_unit_questions"] = other_unit_qs + new_entries
    st.session_state["hq_scenarios_generated"][unit_name] = True

    award_action_once(
        action_key=f"unit_questions:{unit_name}",
        action_type="자기주도 질문 & AI 피드백",
        label=f"[{unit_name}] 질문 {len(new_entries)}개 등록 및 기초·중급·심화 실습 설계 완료",
        xp_gain=30,
        badge_id="question_explorer",
    )
    return new_entries


def evaluate_mission_submission(mission: dict, selected_idx: int, rationale: str) -> dict:
    """
    기초·중급·심화 각 모의실습에 대한 학생의 개인별 선택 + 자기주도 PBL 서술 평가 및
    AI 보건튜터 개인별 피드백 생성.
    """
    m_id = mission["id"]
    prev_sub = st.session_state["hq_submissions"].get(m_id)
    attempts = (prev_sub["attempts"] + 1) if prev_sub else 1

    is_correct = selected_idx == mission["correct_index"]
    clean_rationale = (rationale or "").strip()

    keywords = mission.get("required_keywords", [])
    matched_kw = [kw for kw in keywords if kw in clean_rationale]

    # AI 보건튜터 개인별 맞춤 피드백 생성
    level_label = mission.get("level_label", f"미션 {mission.get('step_num', 1)}")
    selected_exp = mission["option_explanations"][selected_idx]
    correct_opt_text = mission["options"][mission["correct_index"]]

    if is_correct and len(clean_rationale) >= 10:
        kw_note = f"(포함된 핵심 개념: **{', '.join(matched_kw[:4])}**)" if matched_kw else "(자신의 언어로 임상 근거를 성실히 서술함)"
        rationale_status = f"개인 PBL 서술 완료 {kw_note}"
        ai_feedback = (
            f"**[AI 보건튜터 개인별 피드백 — {level_label}]**\n"
            f"1. **임상 판단 및 단서 분석**: 정확한 판단입니다! 상황 속 핵심 단서({', '.join(mission['clinical_clues'][:2])})를 놓치지 않고 올바른 간호 행동을 선택했습니다.\n"
            f"2. **자기주도 서술 피드백**: 학생이 작성한 *\"{clean_rationale}\"* 서술에서 환자안전과 근거 기반 간호(EBN)의 핵심 원리가 잘 드러납니다. {kw_note}\n"
            f"3. **교과서 표준 해설**: {selected_exp}\n"
            f"4. **다음 성장 제안**: 이 판단 근거를 잘 기억해 두었다가 다음 단계 실습 및 모둠원들과의 협력 토의에서 비교해 보세요."
        )
    elif is_correct and len(clean_rationale) < 10:
        rationale_status = "정답 확인 완료 · 개인 서술을 1문장 더 보충하면 피드백이 풍부해집니다"
        ai_feedback = (
            f"**[AI 보건튜터 개인별 피드백 — {level_label}]**\n"
            f"1. **임상 판단 확인**: 올바른 선택지(**{selected_idx + 1}번**)를 골랐습니다! ({selected_exp})\n"
            f"2. **자기주도 서술 코칭**: PBL 학습에서는 '왜 그렇게 판단했는지'를 자신의 말로 설명하는 과정이 가장 중요합니다. "
            f"**[{mission.get('pbl_writing_guide', '관찰 단서와 판단 이유를 한 문장으로 적어보세요.')}]** 힌트를 참고해 서술란을 한 문장으로 채워 다시 눌러보세요!"
        )
    else:
        rationale_status = "재도전 코칭 진행 중 (감점 없음)"
        ai_feedback = (
            f"**[AI 보건튜터 개인별 코칭 — {level_label} (재도전 가이드)]**\n"
            f"1. **선택한 행동 점검**: 방금 고르신 {selected_idx + 1}번 보기는 *{selected_exp}*\n"
            f"2. **놓친 임상 단서 다시 보기**: {mission.get('missed_clue_guide', mission.get('hint', ''))}\n"
            f"3. **서술 보완 가이드**: {mission.get('pbl_writing_guide', '')} 위 단서를 바탕으로 올바른 번호와 근거를 수정해 다시 제출해 보세요."
        )

    result = {
        "mission_id": m_id,
        "level_label": level_label,
        "selected_idx": selected_idx,
        "selected_text": mission["options"][selected_idx],
        "correct_text": correct_opt_text,
        "is_correct": is_correct,
        "rationale": clean_rationale,
        "rationale_status": rationale_status,
        "matched_keywords": matched_kw,
        "ai_individual_feedback": ai_feedback,
        "attempts": attempts,
    }
    st.session_state["hq_submissions"][m_id] = result

    # 단계별 보상 및 배지 지급
    step_num = mission.get("step_num", 1)
    award_action_once(
        action_key=f"mission_submit:{m_id}",
        action_type=f"{level_label} 제출",
        label=f"[{mission['title']}] 개인별 PBL 해결안 제출 및 AI 피드백 확인",
        xp_gain=30,
        badge_id="first_mission" if step_num == 1 else ("evidence_thinker" if step_num == 2 else None),
    )

    scenario = get_current_scenario_data()
    completed, total, _ = get_scenario_progress(scenario)
    if completed == total and total > 0:
        newly_done = award_action_once(
            action_key=f"scenario_complete:{scenario['scenario_id']}",
            action_type="기초·중급·심화 완주",
            label=f"[{scenario['title']}] 기초·중급·심화 3단계 개인 PBL 완수",
            xp_gain=50,
            badge_id="pbl_master",
        )
        if newly_done:
            st.session_state["hq_pending_celebration"] = scenario["title"]

    return result


def submit_team_collaboration_and_get_feedback(
    student_name: str,
    group_name: str,
    individual_summary: str,
    peer_comparison: str,
    team_conclusion: str,
    thought_change: str,
) -> str:
    """팀별 협력 해결안을 저장하고 AI 보건튜터의 팀 피드백을 생성."""
    unit = get_current_unit_data()
    scenario = get_current_scenario_data()

    ai_team_fb = (
        f"**[AI 보건튜터 팀별 협력학습 피드백 — {group_name or '우리 모둠'}]**\n"
        f"- **개인 추론과 모둠 비교의 연결성**: 개인별로 해결한 기초·중급·심화 실습 내용을 바탕으로, 모둠원 간 생각 차이(*\"{peer_comparison or '단서 비교 완료'}\"* )를 분석하여 사각지대를 줄인 점이 매우 우수합니다.\n"
        f"- **팀 최종 해결안 및 우선순위 타당성**: 모둠이 도출한 최종 해결안(*\"{team_conclusion or '환자안전 최우선 간호 행동 합의'}\"* )은 **{unit.get('subject', '보건간호')}** 교육과정의 표준주의·환자안전·법적 업무 경계(비침습적 관찰 및 신속 보고) 원칙에 부합합니다.\n"
        f"- **협업 성장 확인**: 토의를 통해 *\"{thought_change or '근거 기반 판단과 팀 소통의 중요성 확인'}\"* 으로 사고를 확장한 점이 예비 보건의료인의 다학제 협업 역량을 잘 보여줍니다."
    )

    existing_teacher_fb = st.session_state.get("hq_team_notes", {}).get("teacher_feedback", "")
    st.session_state["hq_student_label"] = student_name.strip()
    st.session_state["hq_group_label"] = group_name.strip()
    st.session_state["hq_team_notes"] = {
        "individual_summary": individual_summary.strip(),
        "peer_comparison": peer_comparison.strip(),
        "team_conclusion": team_conclusion.strip(),
        "thought_change": thought_change.strip(),
        "ai_team_feedback": ai_team_fb,
        "teacher_feedback": existing_teacher_fb,
        "saved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    }

    award_action_once(
        action_key=f"team_collab:{scenario['scenario_id']}",
        action_type="팀 협력 해결안 제출",
        label=f"[{scenario['title']}] 팀 협력 해결안 제출 및 AI 팀 피드백 완료",
        xp_gain=40,
        badge_id="team_collaborator",
    )
    return ai_team_fb


def generate_or_save_teacher_feedback(custom_teacher_comment: str = "") -> str:
    """마지막 단계인 '교사의 피드백'을 생성 또는 저장하여 완전학습 루프를 완성."""
    unit_name = st.session_state.get("hq_selected_unit", "")
    scenario = get_current_scenario_data()
    completed, total, _ = get_scenario_progress(scenario)
    qs = get_unit_questions_for_current()

    if custom_teacher_comment and custom_teacher_comment.strip():
        teacher_fb = custom_teacher_comment.strip()
    else:
        teacher_fb = (
            f"[담당 교사 종합 피드백] {unit_name} 단원에서 스스로 {len(qs) or 2}개의 핵심 질문을 던지고, "
            f"기초·중급·심화 모의실습({completed}/{total}단계)을 PBL 근거에 따라 성실히 서술하여 해결했습니다. "
            f"특히 개인별 추론에 그치지 않고 모둠원과의 토의를 통해 환자안전과 예비 보건의료인의 업무 범위(정확한 관찰 및 즉시 보고)를 "
            f"명확히 정립한 점을 높이 평가합니다. 병원 임상실습 현장에서도 오늘 정리한 우선순위 원칙을 꼭 실천하기 바랍니다."
        )

    st.session_state["hq_team_notes"]["teacher_feedback"] = teacher_fb
    award_action_once(
        action_key=f"teacher_feedback:{scenario['scenario_id']}",
        action_type="교사 최종 피드백 확인",
        label=f"[{scenario['title']}] 교사 최종 피드백 확인 및 디지털 학습지 완성",
        xp_gain=30,
    )
    return teacher_fb


def save_mission_reflection(mission: dict, reflection_text: str):
    m_id = mission["id"]
    clean_ref = (reflection_text or "").strip()
    st.session_state["hq_reflections"][m_id] = clean_ref
    if len(clean_ref) >= 5:
        award_action_once(
            action_key=f"reflection:{m_id}",
            action_type="성찰 기록",
            label=f"[{mission['title']}] 성찰 질문 작성 완료",
            xp_gain=15,
        )
