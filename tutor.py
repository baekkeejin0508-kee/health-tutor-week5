"""Week 5~8: Single-Agent & Manager Multi-Agent (Inquiry Coach + Safety Reviewer)."""
from pathlib import Path
from typing import Literal
from uuid import uuid4

from agents import Agent, FileSearchTool, ModelSettings, OpenAIResponsesModel, RunConfig, Runner, SQLiteSession
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parent
STAGES = Literal['시작', '개념이해', '탐구질문', '상황초안', '사례후보',
                 '학생선택', '활동작성', '활동피드백', '수정확인', '교사검토', '성찰']


class CaseCard(BaseModel):
    id: Literal['A', 'B', 'C']
    title: str
    situation: str
    concepts: list[str]
    missing_information: list[str]
    inquiry_focus: str


class LearningSupport(BaseModel):
    explanation: str
    candidates: list[CaseCard]


class TeacherReview(BaseModel):
    needed: bool
    reason: str


class TutorReply(BaseModel):
    stage: STAGES
    analysis: str
    support: LearningSupport
    next_action: str
    teacher_review: TeacherReview


def new_session():
    return SQLiteSession('health_' + uuid4().hex)


INQUIRY_COACH_INSTRUCTIONS = """너는 특성화고등학교 보건간호과 2학년 학생의 탐구 질문과 교과서 개념 적용을 검토하는 전문가(Inquiry Coach)이다.
1. 연결된 Knowledge(교과서 PDF 또는 공공 보건의료 웹 문서)를 검색하여 학생 질문의 개념 정확성, 탐구 가능성, 독립변인·종속변인(또는 핵심 간호 관찰·사정 항목), 교육과정 적합성을 검토한다.
2. 학생 대신 완성된 보고서나 정답을 작성하지 말고, 학생이 스스로 사고를 확장할 수 있는 근거와 개선 방향을 제시한다.
3. Knowledge에서 확인되지 않는 파일명, 페이지 번호, 학교 내부 규정, 의학 수치를 임의로 지어내지 않는다(근거 부족 시 명확히 근거 부족임을 밝힌다)."""

SAFETY_REVIEWER_INSTRUCTIONS = """너는 특성화고등학교 보건간호과 2학년 모의실습 및 과학 실험의 안전성을 검토하는 전문가(Safety Reviewer)이다.
1. 학생이 제안한 실험·실습이나 질문에서 위험 요소(소독제·유해 화학물질 혼합, 학생 간 침습적 처치/주사/채혈, 실제 환자 자가 진단 및 약물 처방·복용량 문의, 감염 위험 등)와 교사·의료인 지도 필요성을 평가한다.
2. 유해 물질 혼합 비율/절차, 침습적 의료행위 수행 절차, 실제 질환에 대한 약물 처방·투약 용량은 절대 안내하지 않는다.
3. 고교 2학년 수준에서 안전하게 수행할 수 있는 비침습적 대체 탐구·모의실습 활동(마네킹 모형 실습, 활력징후 측정, 손 위생 관찰, 문헌 탐구 등)과 안전 수칙을 제안한다."""

MANAGER_ORCHESTRATION_ADDON = """

[MULTI-AGENT MANAGER 협업 규칙 (8주차 확장 - 최우선 준수)]
너는 전문 에이전트 도구를 조율하는 Manager Agent이다. 직접 단독으로 판단하지 말고 반드시 아래 기준에 따라 전문가 도구를 호출하라.
1. 개념 설명, 탐구 질문 타당성·변인 검토, 모의사례 설계, 학교/실습 규정 문의, 교과서/공공문서 Knowledge 확인이 필요한 경우(질문에 'PDF에 없는' 등의 표현이 있어도 임의로 단정하지 말고) 반드시 `review_inquiry` 도구를 호출하여 검색 결과를 확인한 뒤 반영한다.
2. 실습·실험 안전성 평가, 유해 물질/소독제 혼합 위험, 침습적 처치(정맥주사·채혈 등) 위험, 실제 증상/약물 복용 문의, 교사 감독 필요성 판단이 필요한 경우 반드시 `check_safety` 도구를 호출하여 결과를 반영한다.
3. 탐구/보고서 관련 요청과 안전성/침습처치 검토가 함께 있는 복합 질문이면 `review_inquiry`와 `check_safety` 두 전문가를 모두 호출하여 결과를 모순 없이 통합한다.
4. 안전 문제나 근거 부족이 확인되면 `teacher_review.needed = true`로 설정하고 안전 경고를 최우선으로 안내한다.
5. 전문가가 확인하지 않은 Knowledge 내용을 확인했다고 주장하지 않는다."""


def build_agent(model: str, version: str = 'v2', tools: list = None):
    if version not in ('v1', 'v2'):
        raise ValueError('Instructions version must be v1 or v2')
    return Agent(
        name='Med-Inquiry & Case Tutor',
        instructions=(ROOT / f'instructions_{version}.txt').read_text(encoding='utf-8'),
        model=model,
        model_settings=ModelSettings(store=True),
        output_type=TutorReply,
        tools=tools if tools is not None else [],
    )


def build_multi_agent(model: str, version: str = 'v2', tools: list = None):
    """8주차 Manager 패턴 기반 Multi-Agent 생성 (Manager + Inquiry Coach + Safety Reviewer)."""
    if version not in ('v1', 'v2'):
        raise ValueError('Instructions version must be v1 or v2')

    inquiry_agent = Agent(
        name='Inquiry Coach',
        model=model,
        instructions=INQUIRY_COACH_INSTRUCTIONS,
        tools=tools if tools is not None else [],
    )
    safety_agent = Agent(
        name='Safety Reviewer',
        model=model,
        instructions=SAFETY_REVIEWER_INSTRUCTIONS,
    )

    inquiry_tool = inquiry_agent.as_tool(
        tool_name='review_inquiry',
        tool_description='PDF/웹 Knowledge를 기반으로 보건간호 개념, 탐구 질문의 타당성·변인, 모의사례 적합성을 검토한다.',
    )
    safety_tool = safety_agent.as_tool(
        tool_name='check_safety',
        tool_description='보건간호 실습·실험의 위험 요소, 약물·침습 처치 경계, 교사 지도 필요성 및 안전한 대체 활동을 검토한다.',
    )

    base_instructions = (ROOT / f'instructions_{version}.txt').read_text(encoding='utf-8')
    manager = Agent(
        name='Med-Inquiry & Case Manager',
        instructions=base_instructions + MANAGER_ORCHESTRATION_ADDON,
        model=model,
        model_settings=ModelSettings(store=True),
        output_type=TutorReply,
        tools=[inquiry_tool, safety_tool],
    )
    manager._sub_agents_config = {
        'inquiry_agent': inquiry_agent,
        'safety_agent': safety_agent,
    }
    return manager


class CandidateCountError(ValueError):
    """Candidate stage must contain exactly three cards."""


class CandidateOrderError(ValueError):
    """Three candidate ids must be A, B, C in that order."""


class UnexpectedCandidatesError(ValueError):
    """A non-candidate stage returned candidate cards."""


class StructuredOutputValidationError(ValueError):
    """Typed output validation failed; keep field values private."""


def validate_reply(reply: TutorReply):
    cards = reply.support.candidates
    if reply.stage == '사례후보':
        if len(cards) != 3:
            raise CandidateCountError() from None
        if [c.id for c in cards] != ['A', 'B', 'C']:
            raise CandidateOrderError() from None
    elif cards:
        raise UnexpectedCandidatesError() from None
    return reply


class EventLoopClosedError(RuntimeError):
    """Safe diagnostic for a closed event loop."""


class EventLoopMismatchError(RuntimeError):
    """Safe diagnostic for resources belonging to another loop."""


class SessionRecoveryError(RuntimeError):
    """Session rollback failed; start a fresh learning session."""


def classify_runtime_error(exc):
    if isinstance(exc, ValidationError):
        return StructuredOutputValidationError()

    current = exc
    seen = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, RuntimeError):
            message = str(current).lower()
            if 'event loop is closed' in message:
                return EventLoopClosedError()
            if 'different loop' in message or 'different event loop' in message:
                return EventLoopMismatchError()
        current = current.__cause__ or current.__context__

    return exc


async def run_turn(agent, text: str, session):
    previous = await session.get_items()

    try:
        if isinstance(agent.model, str):
            async with AsyncOpenAI() as client:
                shared_model = OpenAIResponsesModel(
                    model=agent.model,
                    openai_client=client,
                )
                sub_cfg = getattr(agent, '_sub_agents_config', None)
                if sub_cfg:
                    cloned_inquiry = sub_cfg['inquiry_agent'].clone(model=shared_model)
                    cloned_safety = sub_cfg['safety_agent'].clone(model=shared_model)
                    request_agent = agent.clone(
                        model=shared_model,
                        tools=[
                            cloned_inquiry.as_tool(
                                tool_name='review_inquiry',
                                tool_description='PDF/웹 Knowledge를 기반으로 보건간호 개념, 탐구 질문의 타당성·변인, 모의사례 적합성을 검토한다.',
                            ),
                            cloned_safety.as_tool(
                                tool_name='check_safety',
                                tool_description='보건간호 실습·실험의 위험 요소, 약물·침습 처치 경계, 교사 지도 필요성 및 안전한 대체 활동을 검토한다.',
                            ),
                        ],
                    )
                else:
                    request_agent = agent.clone(model=shared_model)

                result = await Runner.run(
                    request_agent,
                    text,
                    session=session,
                    max_turns=8,
                    run_config=RunConfig(tracing_disabled=True),
                )
        else:
            result = await Runner.run(
                agent,
                text,
                session=session,
                max_turns=8,
                run_config=RunConfig(tracing_disabled=True),
            )

        reply = validate_reply(result.final_output)

        tool_calls = []
        for item in result.new_items:
            if getattr(item, 'type', '') == 'tool_call_item':
                raw = getattr(item, 'raw_item', None)
                tool_calls.append({
                    'type': type(raw).__name__ if raw else 'ToolCall',
                    'name': getattr(raw, 'name', ''),
                    'arguments': getattr(raw, 'arguments', ''),
                })

        return reply, {
            'stage': reply.stage,
            'new_item_types': [
                getattr(item, 'type', type(item).__name__)
                for item in result.new_items
            ],
            'tool_calls': tool_calls,
            'teacher_review_needed': reply.teacher_review.needed,
            'runtime_revision': 'week8-multiagent-client-per-turn',
        }

    except Exception as exc:
        diagnostic = classify_runtime_error(exc)

        try:
            await session.clear_session()
            if previous:
                await session.add_items(previous)
        except Exception:
            raise SessionRecoveryError() from None

        if diagnostic is not exc:
            raise diagnostic from None
        raise


def reply_to_markdown(reply: TutorReply) -> str:
    parts = [
        f'**현재 단계: {reply.stage}**',
        '**학생 생각 분석**\n' + reply.analysis,
        '**학습 도움**\n' + reply.support.explanation,
    ]

    for card in reply.support.candidates:
        parts.append(
            f'### 가상 사례 {card.id} · {card.title}\n'
            f'{card.situation}\n\n'
            f'- 연결 개념: {", ".join(card.concepts)}\n'
            f'- 추가 확인: {", ".join(card.missing_information)}\n'
            f'- 탐구 관점: {card.inquiry_focus}'
        )

    parts.append('**다음 학생 행동**\n' + reply.next_action)
    label = '교사 확인 필요' if reply.teacher_review.needed else '현재 검토 요청 없음'
    parts.append(f'**교사 확인: {label}**\n{reply.teacher_review.reason}')

    return '\n\n'.join(parts)
