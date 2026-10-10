"""Week 5: one agent, no retrieval tools. Clinical behavior needs live review."""
from pathlib import Path
from typing import Literal
from uuid import uuid4

from agents import Agent, ModelSettings, OpenAIResponsesModel, RunConfig, Runner, SQLiteSession
from openai import AsyncOpenAI
from pydantic import BaseModel

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
    # In-memory SQLite: each browser/test has a unique ID, no shared student_session.
    # Refresh/restart loses history. Export before leaving.
    return SQLiteSession('health_' + uuid4().hex)


def build_agent(model: str, version: str = 'v2'):
    if version not in ('v1', 'v2'):
        raise ValueError('Instructions version must be v1 or v2')
    return Agent(
        name='Med-Inquiry & Case Tutor',
        instructions=(ROOT / f'instructions_{version}.txt').read_text(encoding='utf-8'),
        model=model,
        model_settings=ModelSettings(store=False),
        output_type=TutorReply,
        tools=[],
    )


def validate_reply(reply: TutorReply):
    cards = reply.support.candidates
    if reply.stage == '사례후보':
        if [c.id for c in cards] != ['A', 'B', 'C']:
            raise ValueError('Candidate stage requires exactly A, B, C')
    elif cards:
        raise ValueError('Candidates are only allowed at candidate stage')
    return reply


class EventLoopClosedError(RuntimeError):
    """Safe diagnostic name; never contains provider messages or credentials."""


class EventLoopMismatchError(RuntimeError):
    """Safe diagnostic for resources belonging to another event loop."""


class SessionRecoveryError(RuntimeError):
    """Session rollback failed; start a fresh learning session."""


def classify_runtime_error(exc):
    """Inspect locally, expose only fixed diagnostic names, never raw text."""
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
