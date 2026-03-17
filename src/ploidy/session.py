"""Session management for Ploidy debates.

Defines the data structures for debate sessions:
- Session roles (experienced vs. fresh)
- Session context (what each session knows)

The key design principle: sessions are assigned different context depths.
A deep session gets full context (project history, prior decisions,
accumulated knowledge). A fresh session gets deliberately limited context
(just the decision prompt and essential background). Intermediate sessions
can receive partial context. This N-ary asymmetry is what makes the
debate productive -- ploidy refers to the general concept of chromosome
set count, supporting any number of sessions.
"""

from dataclasses import dataclass
from enum import Enum


class SessionRole(Enum):
    """Role of a session within a debate group.

    EXPERIENCED: Full context -- project history, prior decisions, accumulated knowledge.
    FRESH: Limited context -- just the decision prompt and essential background.
    """

    EXPERIENCED = "experienced"
    FRESH = "fresh"


@dataclass
class SessionContext:
    """The context provided to a debate session.

    Attributes:
        session_id: Unique identifier for this session.
        role: Either EXPERIENCED (full context) or FRESH (limited context).
        base_prompt: The decision prompt shared by all sessions.
        context_documents: Additional context documents provided to this session.
    """

    session_id: str
    role: SessionRole
    base_prompt: str
    context_documents: list[str]
