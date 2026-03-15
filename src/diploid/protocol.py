"""Debate protocol definitions.

Defines the structure and rules of a Diploid debate, including:
- Debate phases and valid transitions between them
- Message types exchanged during debate
- Constraints and termination conditions

The protocol ensures debates are structured rather than free-form,
making disagreements interpretable and convergence tractable.

Phases:
    1. INDEPENDENT  -- Both sessions analyze the prompt independently
    2. POSITION     -- Each session declares their stance
    3. CHALLENGE    -- Each session critiques the other's position
    4. CONVERGENCE  -- Find common ground or articulate irreducible disagreement
    5. COMPLETE     -- Debate concluded, result available
"""

from dataclasses import dataclass
from enum import Enum


class DebatePhase(Enum):
    """Phases of a structured debate."""

    INDEPENDENT = "independent"
    POSITION = "position"
    CHALLENGE = "challenge"
    CONVERGENCE = "convergence"
    COMPLETE = "complete"


@dataclass
class DebateMessage:
    """A single message in the debate protocol.

    Attributes:
        session_id: Which session authored this message.
        phase: The debate phase this message belongs to.
        content: The message content.
        timestamp: When the message was created.
    """

    session_id: str
    phase: DebatePhase
    content: str
    timestamp: str


class DebateProtocol:
    """Manages the state machine of a single debate.

    Enforces valid phase transitions and tracks which sessions
    have submitted their contributions for each phase.
    """

    def __init__(self, debate_id: str, prompt: str) -> None:
        """Initialize a new debate protocol instance.

        Args:
            debate_id: Unique identifier for this debate.
            prompt: The decision prompt both sessions will address.
        """
        pass

    def advance_phase(self) -> DebatePhase:
        """Attempt to advance to the next debate phase.

        Returns:
            The new phase after advancement.

        Raises:
            ProtocolError: If advancement conditions are not met.
        """
        pass

    def submit_message(self, message: DebateMessage) -> None:
        """Submit a message to the current phase.

        Args:
            message: The debate message to record.

        Raises:
            ProtocolError: If the message is not valid for the current phase.
        """
        pass
