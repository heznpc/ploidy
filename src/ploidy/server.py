"""MCP server entry point for Ploidy.

Exposes debate tools via the Model Context Protocol, allowing MCP clients
to initiate debates, submit positions, and retrieve convergence results.

Tools exposed:
- debate/start: Begin a new debate session with a decision prompt
- debate/join: Join an existing debate as the fresh session
- debate/position: Submit a position from a session
- debate/challenge: Submit a challenge to another session's position
- debate/converge: Trigger convergence analysis
- debate/cancel: Cancel a debate in progress
- debate/status: Get current state of a debate
- debate/history: Retrieve past debates and their outcomes
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import UTC, datetime

from mcp.server.auth.provider import AccessToken
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ploidy.convergence import ConvergenceEngine
from ploidy.exceptions import PloidyError, ProtocolError, SessionError
from ploidy.protocol import DebateMessage, DebatePhase, DebateProtocol, SemanticAction
from ploidy.session import SessionContext, SessionRole
from ploidy.store import DebateStore

logger = logging.getLogger("ploidy")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_PORT = int(os.environ.get("PLOIDY_PORT", "8765"))
_MAX_PROMPT_LEN = int(os.environ.get("PLOIDY_MAX_PROMPT_LEN", "10000"))
_MAX_CONTENT_LEN = int(os.environ.get("PLOIDY_MAX_CONTENT_LEN", "50000"))
_MAX_CONTEXT_DOCS = int(os.environ.get("PLOIDY_MAX_CONTEXT_DOCS", "10"))
_MAX_SESSIONS_PER_DEBATE = int(os.environ.get("PLOIDY_MAX_SESSIONS", "5"))
_AUTH_TOKEN = os.environ.get("PLOIDY_AUTH_TOKEN")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class _PloidyTokenVerifier:
    """Simple bearer token verifier using PLOIDY_AUTH_TOKEN env var."""

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify a bearer token against the configured secret."""
        if _AUTH_TOKEN and token == _AUTH_TOKEN:
            return AccessToken(
                token=token,
                client_id="ploidy-client",
                scopes=["debate"],
            )
        return None


_auth_kwargs: dict = {}
if _AUTH_TOKEN:
    _auth_kwargs["token_verifier"] = _PloidyTokenVerifier()
    logger.info("Bearer token auth enabled via PLOIDY_AUTH_TOKEN")

mcp = FastMCP(
    "Ploidy",
    instructions="Cross-session multi-agent debate MCP server. "
    "Same model, different context depths, better decisions.",
    port=_PORT,
    **_auth_kwargs,
)

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_store: DebateStore | None = None
_protocols: dict[str, DebateProtocol] = {}
_sessions: dict[str, SessionContext] = {}
_debate_sessions: dict[str, list[str]] = {}
_session_to_debate: dict[str, str] = {}  # reverse index
_debate_locks: dict[str, asyncio.Lock] = {}


async def _init() -> DebateStore:
    """Lazily initialise the store and recover state from SQLite."""
    global _store
    if _store is None:
        _store = DebateStore()
        await _store.initialize()
        await _recover_state(_store)
    return _store


async def _recover_state(store: DebateStore) -> None:
    """Reconstruct in-memory state from persisted data on startup."""
    active_debates = await store.list_active_debates()
    recovered = 0
    for debate in active_debates:
        debate_id = debate["id"]
        if debate_id in _protocols:
            continue

        protocol = DebateProtocol(debate_id, debate["prompt"])
        sessions = await store.get_sessions(debate_id)
        messages = await store.get_messages(debate_id)

        session_ids = []
        for s in sessions:
            role = (
                SessionRole.EXPERIENCED if s["role"] == "experienced"
                else SessionRole.FRESH
            )
            ctx = SessionContext(
                session_id=s["id"],
                role=role,
                base_prompt=s["base_prompt"],
                context_documents=[],
            )
            _sessions[s["id"]] = ctx
            _session_to_debate[s["id"]] = debate_id
            session_ids.append(s["id"])

        # Replay messages to reconstruct protocol state
        for m in messages:
            phase = DebatePhase(m["phase"])
            # Advance protocol to match message phase
            while protocol.phase != phase:
                try:
                    protocol.advance_phase()
                except ProtocolError:
                    break
            action = SemanticAction(m["action"]) if m["action"] else None
            msg = DebateMessage(
                session_id=m["session_id"],
                phase=phase,
                content=m["content"],
                timestamp=m["timestamp"] or _now(),
                action=action,
            )
            protocol.messages.append(msg)

        # If all positions are in, advance to challenge
        if protocol.phase == DebatePhase.POSITION:
            position_sessions = {
                m.session_id for m in protocol.messages
                if m.phase == DebatePhase.POSITION
            }
            if len(session_ids) >= 2 and set(session_ids) <= position_sessions:
                try:
                    protocol.advance_phase()
                except ProtocolError:
                    pass

        _protocols[debate_id] = protocol
        _debate_sessions[debate_id] = session_ids
        _debate_locks[debate_id] = asyncio.Lock()
        recovered += 1

    if recovered:
        logger.info("Recovered %d active debate(s) from database", recovered)


def _find_debate(session_id: str) -> str:
    """Look up debate_id from a session_id via reverse index."""
    debate_id = _session_to_debate.get(session_id)
    if debate_id is None:
        raise SessionError(f"No debate found for session {session_id}")
    return debate_id


def _get_lock(debate_id: str) -> asyncio.Lock:
    """Get or create a per-debate lock."""
    if debate_id not in _debate_locks:
        _debate_locks[debate_id] = asyncio.Lock()
    return _debate_locks[debate_id]


def _now() -> str:
    """UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def _validate_length(text: str, max_len: int, field: str) -> None:
    """Validate text length, raise ProtocolError if exceeded."""
    if len(text) > max_len:
        raise ProtocolError(
            f"{field} exceeds maximum length ({len(text)} > {max_len})"
        )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=True,
        readOnlyHint=False,
        idempotentHint=False,
    ),
)
async def debate_start(
    prompt: str, context_documents: list[str] | None = None
) -> dict:
    """Begin a new debate session with a decision prompt.

    Creates a debate and an experienced (deep-context) session.
    Share the returned debate_id with the fresh session so it can join.

    Args:
        prompt: The decision question to debate.
        context_documents: Optional documents to give the experienced session.

    Returns:
        Debate and session identifiers.
    """
    store = await _init()

    _validate_length(prompt, _MAX_PROMPT_LEN, "prompt")
    docs = context_documents or []
    if len(docs) > _MAX_CONTEXT_DOCS:
        raise ProtocolError(
            f"Too many context documents ({len(docs)} > {_MAX_CONTEXT_DOCS})"
        )
    for i, doc in enumerate(docs):
        _validate_length(doc, _MAX_CONTENT_LEN, f"context_documents[{i}]")

    debate_id = uuid.uuid4().hex[:12]
    await store.save_debate(debate_id, prompt)

    exp_id = f"{debate_id}-exp-{uuid.uuid4().hex[:6]}"
    exp = SessionContext(
        session_id=exp_id,
        role=SessionRole.EXPERIENCED,
        base_prompt=prompt,
        context_documents=docs,
    )
    await store.save_session(exp_id, debate_id, "experienced", prompt)

    _sessions[exp_id] = exp
    _debate_sessions[debate_id] = [exp_id]
    _session_to_debate[exp_id] = debate_id

    protocol = DebateProtocol(debate_id, prompt)
    _protocols[debate_id] = protocol
    _debate_locks[debate_id] = asyncio.Lock()

    logger.info("Debate started: %s by session %s", debate_id, exp_id)

    return {
        "debate_id": debate_id,
        "session_id": exp_id,
        "role": "experienced",
        "phase": protocol.phase.value,
        "prompt": prompt,
        "message": f"Debate created. Share this debate_id with the Fresh session: {debate_id}",
    }


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=False,
        readOnlyHint=False,
        idempotentHint=False,
    ),
)
async def debate_join(debate_id: str) -> dict:
    """Join an existing debate as the fresh (zero-context) session.

    The fresh session receives only the debate prompt — no project context,
    no prior conversation history. This deliberate context asymmetry is
    the core mechanism of Ploidy.

    Args:
        debate_id: The debate to join (provided by the experienced session).

    Returns:
        Session identifier and the debate prompt.
    """
    store = await _init()

    protocol = _protocols.get(debate_id)
    if protocol is None:
        raise PloidyError(f"Debate {debate_id} not found")

    current_count = len(_debate_sessions.get(debate_id, []))
    if current_count >= _MAX_SESSIONS_PER_DEBATE:
        raise ProtocolError(
            f"Debate already has {current_count} sessions "
            f"(max {_MAX_SESSIONS_PER_DEBATE})"
        )

    fresh_id = f"{debate_id}-fresh-{uuid.uuid4().hex[:6]}"
    fresh = SessionContext(
        session_id=fresh_id,
        role=SessionRole.FRESH,
        base_prompt=protocol.prompt,
        context_documents=[],
    )
    await store.save_session(fresh_id, debate_id, "fresh", protocol.prompt)

    _sessions[fresh_id] = fresh
    _debate_sessions[debate_id].append(fresh_id)
    _session_to_debate[fresh_id] = debate_id

    logger.info("Session %s joined debate %s as fresh", fresh_id, debate_id)

    return {
        "debate_id": debate_id,
        "session_id": fresh_id,
        "role": "fresh",
        "phase": protocol.phase.value,
        "prompt": protocol.prompt,
    }


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=False,
        readOnlyHint=False,
        idempotentHint=False,
    ),
)
async def debate_position(session_id: str, content: str) -> dict:
    """Submit a position from a session.

    Records a session's stance on the debate prompt during the POSITION phase.
    Auto-advances from INDEPENDENT to POSITION on first submission.
    Auto-advances from POSITION to CHALLENGE when all sessions have submitted.

    Args:
        session_id: The session submitting the position.
        content: The position statement.

    Returns:
        Confirmation with current phase info.
    """
    store = await _init()
    _validate_length(content, _MAX_CONTENT_LEN, "content")

    if session_id not in _sessions:
        raise SessionError(f"Session {session_id} not found")

    debate_id = _find_debate(session_id)
    lock = _get_lock(debate_id)

    async with lock:
        protocol = _protocols[debate_id]

        if protocol.phase == DebatePhase.INDEPENDENT:
            protocol.advance_phase()

        if protocol.phase != DebatePhase.POSITION:
            raise ProtocolError(
                f"Cannot submit position in phase {protocol.phase.value}"
            )

        msg = DebateMessage(
            session_id=session_id,
            phase=DebatePhase.POSITION,
            content=content,
            timestamp=_now(),
        )
        protocol.submit_message(msg)
        await store.save_message(debate_id, session_id, "position", content)

        session_ids = set(_debate_sessions[debate_id])
        submitted = {
            m.session_id
            for m in protocol.messages
            if m.phase == DebatePhase.POSITION
        }
        all_in = len(session_ids) >= 2 and session_ids <= submitted

        if all_in:
            protocol.advance_phase()

    logger.info(
        "Position from %s in debate %s (all_in=%s)", session_id, debate_id, all_in
    )

    return {
        "session_id": session_id,
        "debate_id": debate_id,
        "phase": protocol.phase.value,
        "status": "recorded",
        "content_length": len(content),
        "all_positions_in": all_in,
    }


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=False,
        readOnlyHint=False,
        idempotentHint=False,
    ),
)
async def debate_challenge(
    session_id: str, content: str, action: str = "challenge"
) -> dict:
    """Submit a challenge to another session's position.

    Records a session's critique during the CHALLENGE phase.

    Args:
        session_id: The session submitting the challenge.
        content: The challenge or critique text.
        action: Semantic action -- one of 'challenge', 'agree',
                'propose_alternative', or 'synthesize'.

    Returns:
        Confirmation with current phase info.
    """
    store = await _init()
    _validate_length(content, _MAX_CONTENT_LEN, "content")

    if session_id not in _sessions:
        raise SessionError(f"Session {session_id} not found")

    debate_id = _find_debate(session_id)
    lock = _get_lock(debate_id)

    async with lock:
        protocol = _protocols[debate_id]

        if protocol.phase != DebatePhase.CHALLENGE:
            raise ProtocolError(
                f"Cannot submit challenge in phase {protocol.phase.value}"
            )

        try:
            semantic_action = SemanticAction(action)
        except ValueError:
            raise ProtocolError(
                "Invalid action. "
                "Must be one of: agree, challenge, propose_alternative, synthesize"
            )

        msg = DebateMessage(
            session_id=session_id,
            phase=DebatePhase.CHALLENGE,
            content=content,
            timestamp=_now(),
            action=semantic_action,
        )
        protocol.submit_message(msg)
        await store.save_message(debate_id, session_id, "challenge", content, action)

    logger.info(
        "Challenge from %s in debate %s (action=%s)", session_id, debate_id, action
    )

    return {
        "session_id": session_id,
        "debate_id": debate_id,
        "phase": protocol.phase.value,
        "action": action,
        "status": "recorded",
        "content_length": len(content),
    }


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=False,
        readOnlyHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
async def debate_converge(debate_id: str) -> dict:
    """Trigger convergence analysis for a debate.

    Runs the convergence engine on the debate transcript and produces
    a structured synthesis of agreements and disagreements.

    Args:
        debate_id: The debate to analyze.

    Returns:
        Convergence result with synthesis and confidence score.
    """
    store = await _init()

    protocol = _protocols.get(debate_id)
    if protocol is None:
        raise PloidyError(f"Debate {debate_id} not found")

    lock = _get_lock(debate_id)

    async with lock:
        if protocol.phase != DebatePhase.CHALLENGE:
            raise ProtocolError(
                f"Cannot converge from phase {protocol.phase.value}, "
                f"must be in CHALLENGE"
            )

        protocol.advance_phase()  # → CONVERGENCE

        engine = ConvergenceEngine()
        result = await engine.analyze(protocol)

        protocol.advance_phase()  # → COMPLETE

    points_json = json.dumps(
        [
            {
                "category": p.category,
                "summary": p.summary,
                "session_a_view": p.session_a_view,
                "session_b_view": p.session_b_view,
                "resolution": p.resolution,
            }
            for p in result.points
        ]
    )
    await store.save_convergence_and_complete(
        debate_id, result.synthesis, result.confidence, points_json
    )

    # Clean up completed debate from memory
    _cleanup_debate(debate_id)

    logger.info(
        "Debate %s converged (confidence=%.2f, points=%d)",
        debate_id,
        result.confidence,
        len(result.points),
    )

    return {
        "debate_id": debate_id,
        "phase": "complete",
        "synthesis": result.synthesis,
        "confidence": result.confidence,
        "points": [
            {
                "category": p.category,
                "summary": p.summary,
                "resolution": p.resolution,
            }
            for p in result.points
        ],
    }


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=True,
        readOnlyHint=False,
        idempotentHint=True,
    ),
)
async def debate_cancel(debate_id: str) -> dict:
    """Cancel a debate in progress.

    Marks the debate as cancelled and cleans up in-memory state.
    Cannot cancel a completed debate.

    Args:
        debate_id: The debate to cancel.

    Returns:
        Confirmation of cancellation.
    """
    store = await _init()

    protocol = _protocols.get(debate_id)
    if protocol is None:
        raise PloidyError(f"Debate {debate_id} not found")

    if protocol.phase == DebatePhase.COMPLETE:
        raise ProtocolError("Cannot cancel a completed debate")

    await store.update_debate_status(debate_id, "cancelled")
    _cleanup_debate(debate_id)

    logger.info("Debate %s cancelled", debate_id)

    return {
        "debate_id": debate_id,
        "status": "cancelled",
    }


@mcp.tool(
    annotations=ToolAnnotations(
        destructiveHint=True,
        readOnlyHint=False,
        idempotentHint=True,
    ),
)
async def debate_delete(debate_id: str) -> dict:
    """Permanently delete a debate and all its data.

    Removes the debate, its sessions, messages, and convergence results
    from both memory and the database. This action is irreversible.

    Args:
        debate_id: The debate to delete.

    Returns:
        Confirmation of deletion.
    """
    store = await _init()

    debate = await store.get_debate(debate_id)
    if debate is None:
        raise PloidyError(f"Debate {debate_id} not found")

    _cleanup_debate(debate_id)
    await store.delete_debate(debate_id)

    logger.info("Debate %s permanently deleted", debate_id)

    return {
        "debate_id": debate_id,
        "status": "deleted",
    }


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
    ),
)
async def debate_status(debate_id: str) -> dict:
    """Get current state of a debate.

    Returns phase, session info, and all messages for a debate.

    Args:
        debate_id: The debate to inspect.

    Returns:
        Current debate status.
    """
    await _init()

    protocol = _protocols.get(debate_id)
    if protocol is None:
        raise PloidyError(f"Debate {debate_id} not found")

    session_ids = _debate_sessions.get(debate_id, [])
    sessions_info = []
    for sid in session_ids:
        ctx = _sessions.get(sid)
        if ctx:
            sessions_info.append({"session_id": sid, "role": ctx.role.value})

    messages_by_phase: dict[str, list[dict]] = {}
    for msg in protocol.messages:
        phase = msg.phase.value
        if phase not in messages_by_phase:
            messages_by_phase[phase] = []
        messages_by_phase[phase].append(
            {
                "session_id": msg.session_id,
                "content": msg.content,
                "action": msg.action.value if msg.action else None,
                "timestamp": msg.timestamp,
            }
        )

    return {
        "debate_id": debate_id,
        "phase": protocol.phase.value,
        "prompt": protocol.prompt,
        "message_count": len(protocol.messages),
        "sessions": sessions_info,
        "messages": messages_by_phase,
    }


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
    ),
)
async def debate_history(limit: int = 50) -> dict:
    """Retrieve past debates and their outcomes.

    Lists recent debates with their status and convergence results.

    Args:
        limit: Maximum number of debates to return (default 50, max 200).

    Returns:
        List of past debate summaries.
    """
    store = await _init()
    clamped = min(max(limit, 1), 200)
    debates = await store.list_debates(clamped)
    return {
        "debates": debates,
        "total": len(debates),
        "limit": clamped,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _cleanup_debate(debate_id: str) -> None:
    """Remove a completed/cancelled debate from in-memory state."""
    _protocols.pop(debate_id, None)
    _debate_locks.pop(debate_id, None)
    session_ids = _debate_sessions.pop(debate_id, [])
    for sid in session_ids:
        _sessions.pop(sid, None)
        _session_to_debate.pop(sid, None)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the Ploidy MCP server."""
    log_level = os.environ.get("PLOIDY_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    mcp.run(transport="streamable-http")
