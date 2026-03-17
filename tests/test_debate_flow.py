"""End-to-end test for the full debate flow.

Simulates the two-terminal workflow:
1. Deep session starts a debate
2. Fresh session joins
3. Both submit positions
4. Both submit challenges
5. Convergence produces a structured result
"""

import pytest

from ploidy import server


@pytest.fixture(autouse=True)
async def _reset_state():
    """Reset module-level state between tests."""
    server._store = None
    server._protocols.clear()
    server._sessions.clear()
    server._debate_sessions.clear()
    yield
    if server._store is not None:
        await server._store.close()
        server._store = None


async def test_full_debate_flow():
    """Complete debate lifecycle: start → join → positions → challenges → converge."""
    # 1. Deep session starts debate
    start = await server.debate_start(
        prompt="Should we use monorepo or polyrepo?",
        context_documents=["We have 3 teams, 12 microservices"],
    )
    assert start["role"] == "experienced"
    assert start["phase"] == "independent"
    debate_id = start["debate_id"]
    exp_id = start["session_id"]

    # 2. Fresh session joins
    join = await server.debate_join(debate_id)
    assert join["role"] == "fresh"
    assert join["prompt"] == "Should we use monorepo or polyrepo?"
    fresh_id = join["session_id"]

    # 3. Both submit positions
    pos_exp = await server.debate_position(
        session_id=exp_id,
        content="Monorepo. We have shared libs and cross-team dependencies.",
    )
    assert pos_exp["status"] == "recorded"
    assert pos_exp["all_positions_in"] is False
    assert pos_exp["phase"] == "position"

    pos_fresh = await server.debate_position(
        session_id=fresh_id,
        content="Polyrepo. Each service should be independently deployable.",
    )
    assert pos_fresh["status"] == "recorded"
    assert pos_fresh["all_positions_in"] is True
    assert pos_fresh["phase"] == "challenge"  # auto-advanced

    # 4. Check status — both positions visible
    status = await server.debate_status(debate_id)
    assert status["phase"] == "challenge"
    assert status["message_count"] == 2
    assert "position" in status["messages"]
    assert len(status["messages"]["position"]) == 2

    # 5. Both submit challenges
    ch_exp = await server.debate_challenge(
        session_id=exp_id,
        content="Polyrepo ignores our shared auth library. Duplication across 12 repos.",
        action="challenge",
    )
    assert ch_exp["status"] == "recorded"

    ch_fresh = await server.debate_challenge(
        session_id=fresh_id,
        content="Monorepo creates coupling. Independent deployment is more valuable.",
        action="challenge",
    )
    assert ch_fresh["status"] == "recorded"

    # 6. Converge
    result = await server.debate_converge(debate_id)
    assert result["phase"] == "complete"
    assert result["confidence"] is not None
    assert isinstance(result["points"], list)
    assert len(result["points"]) == 2
    assert result["synthesis"]  # non-empty


async def test_start_and_status():
    """Status shows correct info after start."""
    start = await server.debate_start(prompt="Test prompt")
    status = await server.debate_status(start["debate_id"])
    assert status["prompt"] == "Test prompt"
    assert status["phase"] == "independent"
    assert len(status["sessions"]) == 1


async def test_position_before_join_works():
    """Deep session can submit position before fresh joins."""
    start = await server.debate_start(prompt="Test")
    exp_id = start["session_id"]

    pos = await server.debate_position(exp_id, "My position")
    assert pos["status"] == "recorded"
    assert pos["all_positions_in"] is False


async def test_challenge_in_wrong_phase_fails():
    """Cannot submit challenge during position phase."""
    start = await server.debate_start(prompt="Test")
    exp_id = start["session_id"]

    with pytest.raises(Exception, match="Cannot submit challenge"):
        await server.debate_challenge(exp_id, "Challenge!", "challenge")


async def test_converge_in_wrong_phase_fails():
    """Cannot converge before challenge phase."""
    start = await server.debate_start(prompt="Test")

    with pytest.raises(Exception, match="Cannot converge"):
        await server.debate_converge(start["debate_id"])


async def test_agree_action_increases_confidence():
    """Agree actions produce higher confidence than challenges."""
    start = await server.debate_start(prompt="Agree test")
    debate_id = start["debate_id"]
    exp_id = start["session_id"]

    join = await server.debate_join(debate_id)
    fresh_id = join["session_id"]

    await server.debate_position(exp_id, "Position A")
    await server.debate_position(fresh_id, "Position B")

    await server.debate_challenge(exp_id, "I agree with Fresh", "agree")
    await server.debate_challenge(fresh_id, "I agree with Experienced", "agree")

    result = await server.debate_converge(debate_id)
    assert result["confidence"] == 1.0


async def test_cancel_debate():
    """Cancel removes debate from active state."""
    start = await server.debate_start(prompt="Cancel test")
    debate_id = start["debate_id"]

    result = await server.debate_cancel(debate_id)
    assert result["status"] == "cancelled"

    with pytest.raises(Exception, match="not found"):
        await server.debate_status(debate_id)


async def test_delete_debate():
    """Delete removes debate from both memory and database."""
    start = await server.debate_start(prompt="Delete test")
    debate_id = start["debate_id"]

    result = await server.debate_delete(debate_id)
    assert result["status"] == "deleted"

    history = await server.debate_history()
    assert not any(d["id"] == debate_id for d in history["debates"])


async def test_input_validation():
    """Oversized inputs are rejected."""
    with pytest.raises(Exception, match="exceeds maximum length"):
        await server.debate_start(prompt="x" * 20000)


async def test_session_cap():
    """Cannot exceed max sessions per debate."""
    start = await server.debate_start(prompt="Cap test")
    debate_id = start["debate_id"]

    for _ in range(4):
        await server.debate_join(debate_id)

    with pytest.raises(Exception, match="max"):
        await server.debate_join(debate_id)


async def test_persistence():
    """Debates are persisted and appear in history."""
    start = await server.debate_start(prompt="Persist test")
    debate_id = start["debate_id"]
    exp_id = start["session_id"]

    join = await server.debate_join(debate_id)
    fresh_id = join["session_id"]

    await server.debate_position(exp_id, "A")
    await server.debate_position(fresh_id, "B")
    await server.debate_challenge(exp_id, "Challenge A", "challenge")
    await server.debate_challenge(fresh_id, "Challenge B", "challenge")
    await server.debate_converge(debate_id)

    history = await server.debate_history()
    assert history["total"] >= 1
    assert any(d["id"] == debate_id for d in history["debates"])
