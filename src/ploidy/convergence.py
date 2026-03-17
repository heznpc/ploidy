"""Convergence engine for Ploidy debates.

Analyzes the debate transcript to determine:
- Points of agreement (sessions converged independently)
- Points of productive disagreement (a session raised a valid concern)
- Points of irreducible disagreement (genuinely different values/priorities)

The convergence result is a structured synthesis, not a simple
majority vote. The goal is to surface *why* the sessions disagreed,
since context asymmetry makes disagreements interpretable.
"""

from dataclasses import dataclass

from ploidy.exceptions import ConvergenceError
from ploidy.protocol import DebatePhase, DebateProtocol, SemanticAction


@dataclass
class ConvergencePoint:
    """A single point in the convergence analysis.

    Attributes:
        category: One of 'agreement', 'productive_disagreement', 'irreducible'.
        summary: Brief description of the point.
        session_a_view: How the experienced session sees this point.
        session_b_view: How the fresh session sees this point.
        resolution: The synthesized resolution, if any.
    """

    category: str
    summary: str
    session_a_view: str
    session_b_view: str
    resolution: str | None


@dataclass
class ConvergenceResult:
    """The outcome of a debate's convergence analysis.

    Attributes:
        debate_id: The debate this result belongs to.
        points: Individual convergence points identified.
        synthesis: Overall synthesized recommendation.
        confidence: Confidence score for the synthesis (0.0 to 1.0).
    """

    debate_id: str
    points: list[ConvergencePoint]
    synthesis: str
    confidence: float


class ConvergenceEngine:
    """Analyzes debate transcripts and produces convergence results.

    Takes the full debate protocol (with all messages from all sessions)
    and produces a structured analysis of where and why the sessions
    agreed or disagreed.
    """

    async def analyze(
        self,
        protocol: DebateProtocol,
        session_roles: dict[str, str] | None = None,
    ) -> ConvergenceResult:
        """Run convergence analysis on a completed debate.

        Collects positions and challenges, classifies them by semantic action,
        and produces a structured synthesis.

        Args:
            protocol: The debate protocol with all messages.
            session_roles: Optional map of session_id to role display name.

        Returns:
            Structured convergence result.

        Raises:
            ConvergenceError: If the debate is not yet in CONVERGENCE phase.
        """
        if protocol.phase != DebatePhase.CONVERGENCE:
            raise ConvergenceError(
                f"Cannot analyze: debate is in {protocol.phase.value}, expected convergence"
            )

        positions: dict[str, str] = {}
        challenges = []

        for msg in protocol.messages:
            if msg.phase == DebatePhase.POSITION:
                positions[msg.session_id] = msg.content
            elif msg.phase == DebatePhase.CHALLENGE:
                challenges.append(msg)

        session_ids = sorted(positions.keys())

        points: list[ConvergencePoint] = []
        for ch in challenges:
            action = ch.action or SemanticAction.CHALLENGE

            if action in (SemanticAction.AGREE, SemanticAction.SYNTHESIZE):
                category = "agreement"
            else:
                category = "productive_disagreement"

            other_ids = [s for s in session_ids if s != ch.session_id]
            own_view = positions.get(ch.session_id, "")
            other_view = positions.get(other_ids[0], "") if other_ids else ""

            points.append(
                ConvergencePoint(
                    category=category,
                    summary=ch.content[:300],
                    session_a_view=own_view[:500],
                    session_b_view=other_view[:500],
                    resolution=(ch.content if action == SemanticAction.SYNTHESIZE else None),
                )
            )

        if not points and len(session_ids) >= 2:
            points.append(
                ConvergencePoint(
                    category="irreducible",
                    summary="No challenges exchanged — positions stand as stated.",
                    session_a_view=positions.get(session_ids[0], "")[:500],
                    session_b_view=positions.get(session_ids[1], "")[:500],
                    resolution=None,
                )
            )

        agree_count = sum(1 for p in points if p.category == "agreement")
        confidence = agree_count / len(points) if points else 0.0

        synthesis = self._build_synthesis(protocol.prompt, positions, points, session_roles)

        return ConvergenceResult(
            debate_id=protocol.debate_id,
            points=points,
            synthesis=synthesis,
            confidence=confidence,
        )

    def _build_synthesis(
        self,
        prompt: str,
        positions: dict[str, str],
        points: list[ConvergencePoint],
        session_roles: dict[str, str] | None = None,
    ) -> str:
        """Build a human-readable synthesis from debate data.

        Args:
            prompt: The original debate prompt.
            positions: Map of session_id to position content.
            points: Classified convergence points.
            session_roles: Optional map of session_id to role name.

        Returns:
            Formatted synthesis text.
        """
        roles = session_roles or {}
        parts = [f"## Debate: {prompt}\n"]

        for sid, pos in positions.items():
            role = roles.get(sid, f"Session {sid[:8]}")
            parts.append(f"### {role} Session Position\n{pos}\n")

        agree = [p for p in points if p.category == "agreement"]
        disagree = [p for p in points if p.category != "agreement"]

        parts.append("### Analysis")
        parts.append(f"- {len(points)} point(s) analyzed")
        parts.append(f"- {len(agree)} agreement(s), {len(disagree)} disagreement(s)")

        if agree:
            parts.append("\n### Agreements")
            for p in agree:
                parts.append(f"- {p.summary}")

        if disagree:
            parts.append("\n### Productive Disagreements")
            for p in disagree:
                parts.append(f"- {p.summary}")

        return "\n".join(parts)
