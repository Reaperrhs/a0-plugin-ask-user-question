"""In-memory state manager for ask_user_question pending sessions."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QuestionOption:
    label: str
    description: str = ""
    preview: str = ""


@dataclass
class Question:
    question: str
    header: str
    options: List[QuestionOption] = field(default_factory=list)
    multi_select: bool = False


@dataclass
class PendingSession:
    session_id: str
    context_id: str
    questions: List[Question]
    created_at: float = field(default_factory=time.time)
    event: asyncio.Event = field(default_factory=asyncio.Event)
    result: Optional[Dict[str, Any]] = None


# Global in-memory store: context_id -> PendingSession
_pending: Dict[str, PendingSession] = {}

# Max age for sessions before cleanup (seconds)
_MAX_AGE = 600


def create_session(
    context_id: str,
    questions: List[Dict[str, Any]],
) -> PendingSession:
    """Create a new pending question session for a context."""
    # Remove any existing session for this context
    if context_id in _pending:
        old = _pending[context_id]
        if old.result is None:
            old.result = {"cancelled": True, "reason": "superseded"}
        old.event.set()

    parsed_questions: List[Question] = []
    for q in questions:
        opts = [
            QuestionOption(
                label=o.get("label", ""),
                description=o.get("description", ""),
                preview=o.get("preview", ""),
            )
            for o in q.get("options", [])
        ]
        parsed_questions.append(
            Question(
                question=q.get("question", ""),
                header=q.get("header", "Q"),
                options=opts,
                multi_select=q.get("multiSelect", False),
            )
        )

    session = PendingSession(
        session_id=str(uuid.uuid4()),
        context_id=context_id,
        questions=parsed_questions,
    )
    _pending[context_id] = session
    return session


def get_pending(context_id: str) -> Optional[PendingSession]:
    """Get the pending session for a context, if any."""
    return _pending.get(context_id)


def submit_answer(
    session_id: str,
    answers: List[Dict[str, Any]],
    cancelled: bool = False,
) -> Optional[PendingSession]:
    """Submit answers for a pending session and signal the waiting tool."""
    for ctx_id, session in _pending.items():
        if session.session_id == session_id:
            if cancelled:
                session.result = {
                    "cancelled": True,
                    "reason": "user_declined",
                }
            else:
                session.result = {
                    "cancelled": False,
                    "answers": answers,
                }
            session.event.set()
            return session
    return None


def cancel_session(session_id: str) -> bool:
    """Cancel a pending session."""
    for ctx_id, session in list(_pending.items()):
        if session.session_id == session_id:
            session.result = {"cancelled": True, "reason": "cancelled"}
            session.event.set()
            if ctx_id in _pending:
                del _pending[ctx_id]
            return True
    return False


def cleanup_old_sessions() -> int:
    """Remove sessions older than _MAX_AGE. Returns count removed."""
    now = time.time()
    to_remove = [
        ctx_id
        for ctx_id, s in _pending.items()
        if now - s.created_at > _MAX_AGE
    ]
    for ctx_id in to_remove:
        s = _pending.pop(ctx_id, None)
        if s and s.result is None:
            s.result = {"cancelled": True, "reason": "timeout"}
            s.event.set()
    return len(to_remove)

