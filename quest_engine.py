"""HEALTH QUEST — 예비 보건의료인의 미션룸: 채점·보상·성장 기록 및 상태 관리 엔진."""
from datetime import datetime, timezone
import streamlit as st
from quest_data import UNIT_CATALOG

BADGE_DEFINITIONS = {
    "first_mission": {
        "id": "first_mission",
        "title": "첫 임상 미션 돌파",
        "desc": "첫 번째 보건 현장 미션을 끝까지 수행하고 피드백을 확인했습니다.",
        "competency": "자기주도학습 역량",
    },
    "evidence_thinker": {
        "id": "evidence_thinker",
        "title": "근거 기반 추론가",
        "desc": "단순 선택을 넘어 임상적 판단 근거를 자신의 말로 논리적으로 작성했습니다.",
        "competency": "임상 문제해결 역량",
    },
    "reflective_improver": {
        "id": "reflective_improver",
        "title": "피드백 성찰·개선가",
        "desc": "피드백과 단서를 확인한 뒤 재도전·보완을 통해 판단을 개선했습니다.",
        "competency": "비판적 성찰 역량",
    },
    "pbl_master": {
        "id": "pbl_master",
        "title": "PBL 모의실습 완주",
        "desc": "선택한 가상 실습 상황의 3단계 미션을 모두 완수하여 완전학습에 도달했습니다.",
        "competency": "현장 실무 통합 역량",
    },
    "team_collaborator": {
        "id": "team_collaborator",
        "title": "협력적 문제해결 팀원",
        "desc": "팀원과 근거를 비교하고 공동 해결안 및 생각의 변화를 기록했습니다.",
        "competency": "보건의료 협업 역량",
    },
}


def init_quest_state():
    """세션 상태 초기화 (새로고침 전까지 현재 브라우저 세션에서 유지)."""
    defaults = {
        "hq_site_title": "HEALTH QUEST — 예비 보건의료인의 미션룸",
        "hq_nav_view": "🏠 미션룸 홈",
        "hq_selected_unit": "감염관리 (표준주의와 격리간호)",
        "hq_selected_scenario_id": "INF_A",
        "hq_active_mission_idx": 0,  # 0, 1, 2
        "hq_reduce_motion": False,
        # 미션별 제출 및 피드백 기록: {mission_id: {...}}
        "hq_submissions": {},
        # 미션별 성찰 기록: {mission_id: str}
        "hq_reflections": {},
        # 중복 보상 방지 키 집합 (set 대신 JSON 직렬화 호환을 위해 list/dict 병행)
        "hq_rewarded_keys": [],
        "hq_xp": 0,
        "hq_growth_log": [],
        "hq_earned_badges": [],
        "hq_pending_badge_notice": None,
        "hq_celebrated_scenarios": [],
        "hq_pending_celebration": None,
        # 단원 질문 & AI 보건튜터 피드백 이력
        "hq_unit_questions": [],
        # 협력학습 (시연 모드) 데이터
        "hq_team_notes": {
            "my_summary": "",
            "peer_comparison": "",
            "team_conclusion": "",
            "team_rationale": "",
            "thought_change": "",
            "saved_at": None,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_current_unit_data() -> dict:
    unit_name = st.session_state.get("hq_selected_unit", "감염관리 (표준주의와 격리간호)")
    return UNIT_CATALOG.get(unit_name, next(iter(UNIT_CATALOG.values())))


def get_current_scenario_data() -> dict:
    unit = get_current_unit_data()
    scen_id = st.session_state.get("hq_selected_scenario_id", "INF_A")
    for s in unit["scenarios"]:
        if s["scenario_id"] == scen_id:
            return s
    st.session_state["hq_selected_scenario_id"] = unit["scenarios"][0]["scenario_id"]
    return unit["scenarios"][0]


def award_action_once(action_key: str, action_type: str, label: str, xp_gain: int, badge_id: str | None = None):
    """중복 제출·페이지 재실행 시 경험치와 배지가 중복 지급되지 않도록 보장."""
    rewarded = st.session_state.get("hq_rewarded_keys", [])
    if action_key not in rewarded:
        rewarded.append(action_key)
        st.session_state["hq_rewarded_keys"] = rewarded
        st.session_state["hq_xp"] = st.session_state.get("hq_xp", 0) + xp_gain
        st.session_state["hq_growth_log"].append(
            {
                "key": action_key,
                "type": action_type,
                "label": label,
                "xp": xp_gain,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        )

    if badge_id and badge_id in BADGE_DEFINITIONS:
        earned = st.session_state.get("hq_earned_badges", [])
        if badge_id not in earned:
            earned.append(badge_id)
            st.session_state["hq_earned_badges"] = earned
            st.session_state["hq_pending_badge_notice"] = BADGE_DEFINITIONS[badge_id]


def evaluate_mission_submission(mission: dict, selected_idx: int, rationale_text: str) -> dict:
    """객관식 정답 여부와 서술형 판단 근거를 구분하여 채점·코칭하고 성장 행동을 기록."""
    m_id = mission["id"]
    prev_sub = st.session_state["hq_submissions"].get(m_id)
    attempt_count = (prev_sub["attempts"] + 1) if prev_sub else 1
    was_previously_submitted = prev_sub is not None

    is_correct = selected_idx == mission["correct_index"]
    clean_rationale = rationale_text.strip()

    # 서술형 근거 평가 (자동 키워드 점검 + 교사 확인 상태 명시)
    matched_kw = [kw for kw in mission.get("required_keywords", []) if kw in clean_rationale]
    has_meaningful_rationale = len(clean_rationale) >= 12

    if not clean_rationale:
        rationale_status = "근거 미작성 — 왜 이 선택지를 골랐는지 환자 안전·교과서 원리로 1문장 이상 적어 보세요."
        rationale_level = "needs_input"
    elif len(matched_kw) >= 2 and len(clean_rationale) >= 15:
        rationale_status = (
            f"핵심 개념({', '.join(matched_kw[:3])})을 포함하여 논리적으로 작성했습니다. "
            f"[최종 서술형 평가: {mission['teacher_review_status']}]"
        )
        rationale_level = "strong"
    else:
        rationale_status = (
            f"나의 생각을 작성했습니다(포함 키워드: {', '.join(matched_kw) if matched_kw else '자유 서술'}). "
            "해설의 핵심 원리와 비교해 보완해 보세요. [서술형 평가: 교사 확인 대상]"
        )
        rationale_level = "partial"

    submission_record = {
        "mission_id": m_id,
        "selected_idx": selected_idx,
        "selected_text": mission["options"][selected_idx],
        "is_correct": is_correct,
        "rationale": clean_rationale,
        "rationale_status": rationale_status,
        "rationale_level": rationale_level,
        "matched_keywords": matched_kw,
        "attempts": attempt_count,
        "teacher_review_status": mission["teacher_review_status"],
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    st.session_state["hq_submissions"][m_id] = submission_record

    # 1) 근거 작성 보상 (정답 빨리 찍기보다 근거 설명을 인정)
    if has_meaningful_rationale:
        award_action_once(
            action_key=f"rationale:{m_id}",
            action_type="근거 작성",
            label=f"[{mission['title']}] 임상 판단 근거 서술 완료",
            xp_gain=25,
            badge_id="evidence_thinker",
        )

    # 2) 피드백 확인 후 수정·재도전 보상
    if was_previously_submitted and (is_correct or len(clean_rationale) > len(prev_sub.get("rationale", ""))):
        award_action_once(
            action_key=f"retry_improve:{m_id}",
            action_type="피드백 후 개선",
            label=f"[{mission['title']}] 피드백 반영 및 재도전 개선 완료",
            xp_gain=30,
            badge_id="reflective_improver",
        )

    # 3) 미션 완료 보상 (정답 + 근거 10자 이상 충족 시 완료 인정)
    if is_correct and len(clean_rationale) >= 5:
        award_action_once(
            action_key=f"mission_clear:{m_id}",
            action_type="미션 완료",
            label=f"[{mission['title']}] 미션 해결 완료",
            xp_gain=35,
            badge_id="first_mission",
        )

    # 4) 현재 시나리오의 전체 3개 미션 모두 완료 시 1회 축하 효과 및 배지 지급
    scenario = get_current_scenario_data()
    all_m_ids = [m["id"] for m in scenario["missions"]]
    all_cleared = all(
        st.session_state["hq_submissions"].get(mid, {}).get("is_correct")
        and len(st.session_state["hq_submissions"].get(mid, {}).get("rationale", "")) >= 5
        for mid in all_m_ids
    )
    if all_cleared:
        scen_id = scenario["scenario_id"]
        award_action_once(
            action_key=f"scenario_complete:{scen_id}",
            action_type="전체 미션 완료",
            label=f"[{scenario['title']}] 3단계 미션 전체 완주 (완전학습 도달)",
            xp_gain=50,
            badge_id="pbl_master",
        )
        if scen_id not in st.session_state["hq_celebrated_scenarios"]:
            st.session_state["hq_celebrated_scenarios"].append(scen_id)
            st.session_state["hq_pending_celebration"] = scenario["title"]

    return submission_record


def save_mission_reflection(mission: dict, reflection_text: str):
    clean = reflection_text.strip()
    if not clean:
        return False
    m_id = mission["id"]
    st.session_state["hq_reflections"][m_id] = clean
    award_action_once(
        action_key=f"reflection:{m_id}",
        action_type="성찰 기록",
        label=f"[{mission['title']}] 임상 성찰 질문 작성 완료",
        xp_gain=20,
    )
    return True


def generate_unit_inquiry_feedback(unit_data: dict, student_question: str, student_level: str) -> dict:
    """학생의 단원 질문·용어 궁금증에 대해 단계별 AI 보건튜터 피드백과 가상 실습 상황 3개 연결 가이드를 생성."""
    q = student_question.strip()
    # 위험/금기 키워드 감지 (안전 경계)
    safety_keywords = ["락스", "섞", "혼합", "주사", "채혈", "무슨 약", "약 추천", "복용량", "대신 써", "다 써줘"]
    needs_safety_alert = any(kw in q for kw in safety_keywords)

    matched_terms = []
    for term_name, term_desc in unit_data["key_terms"].items():
        core_word = term_name.split("(")[0].strip()
        if core_word in q:
            matched_terms.append((term_name, term_desc))

    if not matched_terms:
        # 기본 핵심 용어 2개 안내
        matched_terms = list(unit_data["key_terms"].items())[:2]

    if needs_safety_alert:
        safety_note = (
            "⚠️ **[Safety Reviewer 안전 경계 안내]** 소독제 임의 혼합, 학생 간 침습적 시술(주사·채혈), "
            "실제 환자에 대한 약물 처방·복용량 안내는 환자 안전과 법적 경계에 따라 금지되어 있습니다. "
            "교사 감독하에 마네킹 모형이나 비침습적 관찰·교육 실습으로 안전하게 전환하여 탐구해 봅시다. [교사 검토 필요]"
        )
    else:
        safety_note = "✅ **[안전성 확인]** 고등학교 보건간호과 2학년 모의실습 범위(비침습적 사정, 표준주의, 환자 교육)에 적합한 안전한 탐구 주제입니다."

    feedback_steps = [
        f"**1단계 (질문 의도 및 눈높이 개념 연결 · {student_level})**: 질문하신 '{q}' 주제는 `{unit_data['badge']}`에서 환자 안전과 직결되는 핵심 개념입니다.",
        "**2단계 (핵심 의학용어·원리 짚어보기)**:\n"
        + "\n".join([f"- **{t}**: {d}" for t, d in matched_terms]),
        f"**3단계 (안전 및 교육과정 적합성)**: {safety_note}",
        "**4단계 (가상 실습 상황 3가지 연결)**: 아래 제시된 **가상 실습 상황 A, B, C** 중 질문하신 개념을 직접 적용해 보고 싶은 **최종 1가지 상황**을 선택해 3단계 미션에 도전해 보세요!",
    ]

    record = {
        "unit": unit_data["unit_id"],
        "level": student_level,
        "question": q,
        "feedback_markdown": "\n\n".join(feedback_steps),
        "teacher_review_needed": needs_safety_alert,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }
    st.session_state["hq_unit_questions"].append(record)
    award_action_once(
        action_key=f"unit_question:{unit_data['unit_id']}",
        action_type="탐구 질문 작성",
        label=f"[{unit_data['unit_id']}] 단원 개념·용어 탐구 질문 등록",
        xp_gain=15,
    )
    return record


def get_scenario_progress(scenario: dict) -> tuple[int, int, float]:
    missions = scenario["missions"]
    total = len(missions)
    completed = 0
    for m in missions:
        sub = st.session_state["hq_submissions"].get(m["id"])
        if sub and sub.get("is_correct") and len(sub.get("rationale", "")) >= 5:
            completed += 1
    ratio = (completed / total) if total else 0.0
    return completed, total, ratio


def build_quest_export_payload() -> dict:
    """학생·교사 다운로드용 전체 학습 결과 데이터 생성."""
    scenario = get_current_scenario_data()
    completed, total, ratio = get_scenario_progress(scenario)
    return {
        "notice": "HEALTH QUEST 모의실습 학습 기록 (현재 브라우저 세션 기록이며 개인 건강정보 미포함)",
        "persistence_scope": "세션 내 st.session_state 기록 (영구 보관을 위해 본 JSON/TXT 파일 다운로드 사용)",
        "site_title": st.session_state.get("hq_site_title"),
        "selected_unit": st.session_state.get("hq_selected_unit"),
        "selected_scenario": scenario["title"],
        "progress": f"{completed}/{total} ({int(ratio * 100)}%)",
        "xp": st.session_state.get("hq_xp", 0),
        "earned_badges": [BADGE_DEFINITIONS[b]["title"] for b in st.session_state.get("hq_earned_badges", []) if b in BADGE_DEFINITIONS],
        "unit_questions": st.session_state.get("hq_unit_questions", []),
        "mission_submissions": st.session_state.get("hq_submissions", {}),
        "mission_reflections": st.session_state.get("hq_reflections", {}),
        "team_collaboration": st.session_state.get("hq_team_notes", {}),
        "growth_log": st.session_state.get("hq_growth_log", []),
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
    }

