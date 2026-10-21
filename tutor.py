"""Week 5: one agent, no retrieval tools. Clinical behavior needs live review."""
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


def build_agent(model: str, version: str = 'v2', tools: list = None):
    if version not in ('v1', 'v2'):
        raise ValueError('Instructions version must be v1 or v2')
    return Agent(
        name='Med-Inquiry & Case Tutor',
        instructions=(ROOT / f'instructions_{version}.txt').read_text(encoding='utf-8'),
        model=model,
        model_settings=ModelSettings(store=False),
        output_type=TutorReply,
        tools=tools if tools is not None else [],
    )


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
                request_agent = agent.clone(model=OpenAIResponsesModel(
                    model=agent.model,
                    openai_client=client,
                ))
                result = await Runner.run(
                    request_agent,
                    text,
                    session=session,
                    max_turns=3,
                    run_config=RunConfig(tracing_disabled=True),
                )
        else:
            result = await Runner.run(
                agent,
                text,
                session=session,
                max_turns=3,
                run_config=RunConfig(tracing_disabled=True),
            )

        reply = validate_reply(result.final_output)

        return reply, {
            'stage': reply.stage,
            'new_item_types': [
                getattr(item, 'type', type(item).__name__)
                for item in result.new_items
            ],
            'teacher_review_needed': reply.teacher_review.needed,
            'runtime_revision': 'week5-client-per-turn-diagnostics-2',
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
