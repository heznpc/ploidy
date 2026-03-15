"""Session management for Diploid debates.

Handles the lifecycle of debate sessions, including:
- Creating session pairs (experienced + fresh) for a debate
- Managing context injection -- what each session knows
- Tracking session state across the debate lifecycle

The key design principle: Session A gets full context (project history,
prior decisions, accumulated knowledge). Session B gets deliberately
limited context (just the decision prompt and essential background).
This asymmetry is what makes the debate productive.
"""

from dataclasses import dataclass


@dataclass
class SessionContext:
    """The context provided to a debate session.

    Attributes:
        session_id: Unique identifier for this session.
        role: Either 'experienced' (full context) or 'fresh' (limited context).
        base_prompt: The decision prompt shared by both sessions.
        context_documents: Additional context documents provided to this session.
    """

    session_id: str
    role: str
    base_prompt: str
    context_documents: list[str]


class SessionManager:
    """Manages debate session pairs and their context.

    Creates and tracks session pairs for each debate, ensuring
    proper context asymmetry between the experienced and fresh sessions.
    """

    def __init__(self, store: object) -> None:
        """Initialize the session manager.

        Args:
            store: Persistence layer for session data.
        """
        pass

    async def create_session_pair(
        self,
        debate_id: str,
        prompt: str,
        full_context: list[str],
    ) -> tuple[SessionContext, SessionContext]:
        """Create an experienced/fresh session pair for a debate.

        Args:
            debate_id: The debate these sessions belong to.
            prompt: The decision prompt for both sessions.
            full_context: Complete context documents (given only to Session A).

        Returns:
            Tuple of (experienced_session, fresh_session).
        """
        pass

    async def get_session(self, session_id: str) -> SessionContext | None:
        """Retrieve a session by its ID.

        Args:
            session_id: The session to look up.

        Returns:
            The session context, or None if not found.
        """
        pass
