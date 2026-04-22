"""Unit tests for the convergence engine."""

import pytest

from ploidy.convergence import ConvergenceEngine
from ploidy.protocol import DebateMessage, DebatePhase, DebateProtocol, SemanticAction


def _make_protocol(
    *,
    phase: DebatePhase = DebatePhase.CONVERGENCE,
    messages: list[DebateMessage] | None = None,
) -> DebateProtocol:
    """Build a minimal DebateProtocol for testing."""
    proto = DebateProtocol(debate_id="test-debate", prompt="Should we use Rust?")
    proto.phase = phase
    if messages:
        proto.messages = messages
    return proto


def _msg(session_id: str, phase: DebatePhase, content: str, action=None) -> DebateMessage:
    return DebateMessage(
        session_id=session_id,
        phase=phase,
        content=content,
        timestamp="2026-01-01T00:00:00",
        action=action,
    )


class TestConvergenceEngine:
    """Tests for rule-based convergence."""

    async def test_wrong_phase_raises(self):
        proto = _make_protocol(phase=DebatePhase.POSITION)
        engine = ConvergenceEngine()
        with pytest.raises(Exception, match="expected convergence"):
            await engine.analyze(proto)

    async def test_no_challenges_emits_informational_point(self):
        """No challenges → a ``no_challenges`` marker, not a disagreement."""
        proto = _make_protocol(
            messages=[
                _msg("deep", DebatePhase.POSITION, "Rust is fast"),
                _msg("fresh", DebatePhase.POSITION, "Go is simpler"),
            ],
        )
        engine = ConvergenceEngine()
        result = await engine.analyze(proto)
        assert len(result.points) == 1
        assert result.points[0].category == "no_challenges"
        # Confidence is still a float (0.0 for DB-schema compat), but
        # the renderer understands to suppress the number.
        assert result.confidence == 0.0

    async def test_no_challenges_point_excluded_from_confidence_denominator(self):
        """Agreement + a no_challenges marker computes confidence over 1, not 2."""
        proto = _make_protocol(
            messages=[
                _msg("deep", DebatePhase.POSITION, "Rust is fast"),
                _msg("fresh", DebatePhase.POSITION, "Rust is safe"),
                _msg("fresh", DebatePhase.CHALLENGE, "Agree", SemanticAction.AGREE),
            ],
        )
        engine = ConvergenceEngine()
        result = await engine.analyze(proto)
        assert result.confidence == 1.0

    async def test_agree_action_classified_as_agreement(self):
        proto = _make_protocol(
            messages=[
                _msg("deep", DebatePhase.POSITION, "Rust is fast"),
                _msg("fresh", DebatePhase.POSITION, "Rust is safe"),
                _msg("fresh", DebatePhase.CHALLENGE, "I agree", SemanticAction.AGREE),
            ],
        )
        engine = ConvergenceEngine()
        result = await engine.analyze(proto)
        assert result.points[0].category == "agreement"
        assert result.confidence == 1.0

    async def test_challenge_action_classified_as_disagreement(self):
        proto = _make_protocol(
            messages=[
                _msg("deep", DebatePhase.POSITION, "PostgreSQL is fine"),
                _msg("fresh", DebatePhase.POSITION, "Consider TimescaleDB"),
                _msg("fresh", DebatePhase.CHALLENGE, "Sunk cost fallacy", SemanticAction.CHALLENGE),
            ],
        )
        engine = ConvergenceEngine()
        result = await engine.analyze(proto)
        assert result.points[0].category == "productive_disagreement"
        assert result.confidence == 0.0

    async def test_synthesize_counted_as_agreement(self):
        proto = _make_protocol(
            messages=[
                _msg("deep", DebatePhase.POSITION, "Use PostgreSQL"),
                _msg("fresh", DebatePhase.POSITION, "Use TimescaleDB"),
                _msg("deep", DebatePhase.CHALLENGE, "Both have merit", SemanticAction.SYNTHESIZE),
            ],
        )
        engine = ConvergenceEngine()
        result = await engine.analyze(proto)
        assert result.points[0].category == "agreement"
        assert result.points[0].resolution is not None

    async def test_mixed_actions_confidence(self):
        proto = _make_protocol(
            messages=[
                _msg("deep", DebatePhase.POSITION, "A"),
                _msg("fresh", DebatePhase.POSITION, "B"),
                _msg("fresh", DebatePhase.CHALLENGE, "Agree", SemanticAction.AGREE),
                _msg("deep", DebatePhase.CHALLENGE, "Disagree", SemanticAction.CHALLENGE),
            ],
        )
        engine = ConvergenceEngine()
        result = await engine.analyze(proto)
        assert result.confidence == pytest.approx(0.5)

    async def test_synthesis_text_contains_positions(self):
        proto = _make_protocol(
            messages=[
                _msg("deep", DebatePhase.POSITION, "Rust is fast"),
                _msg("fresh", DebatePhase.POSITION, "Go is simpler"),
                _msg(
                    "fresh", DebatePhase.CHALLENGE, "Speed vs simplicity", SemanticAction.CHALLENGE
                ),
            ],
        )
        engine = ConvergenceEngine()
        roles = {"deep": "Experienced", "fresh": "Fresh"}
        result = await engine.analyze(proto, session_roles=roles)
        assert "Experienced" in result.synthesis
        assert "Fresh" in result.synthesis
        assert "Rust" in result.synthesis


class TestExtractConfidence:
    """Tests for _extract_confidence regex parsing."""

    def setup_method(self):
        self.engine = ConvergenceEngine()

    def test_parses_confidence_colon_format(self):
        assert self.engine._extract_confidence("confidence: 0.85") == pytest.approx(0.85)

    def test_parses_score_format(self):
        assert self.engine._extract_confidence("Overall score: 0.7") == pytest.approx(0.7)

    def test_clamps_above_one(self):
        assert self.engine._extract_confidence("confidence: 1.5") == pytest.approx(1.0)

    def test_returns_none_for_no_match(self):
        assert self.engine._extract_confidence("no numbers here") is None

    def test_handles_integer_one(self):
        assert self.engine._extract_confidence("confidence: 1") == pytest.approx(1.0)

    def test_handles_zero(self):
        assert self.engine._extract_confidence("confidence: 0.0") == pytest.approx(0.0)


class TestAlternativeAction:
    """PROPOSE_ALTERNATIVE lands in the ``else`` branch of the action switch."""

    async def test_propose_alternative_classified_as_productive(self):
        proto = _make_protocol(
            messages=[
                _msg("s1", DebatePhase.POSITION, "Use Rust"),
                _msg("s2", DebatePhase.POSITION, "Use Go"),
                _msg(
                    "s1",
                    DebatePhase.CHALLENGE,
                    "PROPOSE_ALTERNATIVE: ship Go now, migrate later",
                    action=SemanticAction.PROPOSE_ALTERNATIVE,
                ),
            ],
        )
        engine = ConvergenceEngine()
        result = await engine.analyze(proto)
        # PROPOSE_ALTERNATIVE must not collapse into the CHALLENGE branch —
        # mutual-challenge detection does not apply here.
        assert result.points[0].category == "productive_disagreement"


class TestLlmMetaAnalysis:
    """LLM-enhanced meta-analysis path (use_llm=True)."""

    async def test_api_unavailable_returns_none_without_calling_api(self, monkeypatch):
        from ploidy import api_client

        # Force the availability check to report False even if env has a URL.
        monkeypatch.setattr(api_client, "is_api_available", lambda: False)

        proto = _make_protocol(
            messages=[
                _msg("s1", DebatePhase.POSITION, "A"),
                _msg("s2", DebatePhase.POSITION, "B"),
            ],
        )
        engine = ConvergenceEngine(use_llm=True)
        result = await engine.analyze(proto)
        assert result.meta_analysis is None

    async def test_success_path_stores_meta_and_averages_confidence(self, monkeypatch):
        from ploidy import api_client

        monkeypatch.setattr(api_client, "is_api_available", lambda: True)

        async def fake_analyze(*, debate_prompt, positions, challenges, session_roles):
            # Echo the inputs into a string that exercises _extract_confidence.
            return f"meta for {len(positions)} positions, confidence: 1.0"

        monkeypatch.setattr(api_client, "analyze_convergence", fake_analyze)

        # One agreement → base confidence 1.0. LLM says 1.0 too → avg 1.0.
        proto = _make_protocol(
            messages=[
                _msg("s1", DebatePhase.POSITION, "A"),
                _msg("s2", DebatePhase.POSITION, "B"),
                _msg("s1", DebatePhase.CHALLENGE, "AGREE", action=SemanticAction.AGREE),
            ],
        )
        engine = ConvergenceEngine(use_llm=True)
        result = await engine.analyze(proto)
        assert result.meta_analysis == "meta for 2 positions, confidence: 1.0"
        assert result.confidence == pytest.approx(1.0)

    async def test_llm_confidence_averages_with_rule_based(self, monkeypatch):
        from ploidy import api_client

        monkeypatch.setattr(api_client, "is_api_available", lambda: True)

        async def fake_analyze(**_):
            return "analysis text, confidence: 0.0"

        monkeypatch.setattr(api_client, "analyze_convergence", fake_analyze)

        # Mutual challenge → rule-based confidence 0.0 (irreducible).
        # LLM says 0.0 too → avg 0.0. But we verify the averaging path runs.
        proto = _make_protocol(
            messages=[
                _msg("s1", DebatePhase.POSITION, "A"),
                _msg("s2", DebatePhase.POSITION, "B"),
                _msg("s1", DebatePhase.CHALLENGE, "AGREE", action=SemanticAction.AGREE),
            ],
        )
        engine = ConvergenceEngine(use_llm=True)
        result = await engine.analyze(proto)
        # (1.0 + 0.0) / 2.0 = 0.5 — proves the averaging branch ran.
        assert result.confidence == pytest.approx(0.5)

    async def test_analyze_convergence_exception_is_swallowed(self, monkeypatch):
        from ploidy import api_client

        monkeypatch.setattr(api_client, "is_api_available", lambda: True)

        async def boom(**_):
            raise RuntimeError("network down")

        monkeypatch.setattr(api_client, "analyze_convergence", boom)

        proto = _make_protocol(
            messages=[
                _msg("s1", DebatePhase.POSITION, "A"),
                _msg("s2", DebatePhase.POSITION, "B"),
            ],
        )
        engine = ConvergenceEngine(use_llm=True)
        # Must not raise — a flaky API should never break convergence.
        result = await engine.analyze(proto)
        assert result.meta_analysis is None

    async def test_missing_api_client_module_returns_none(self, monkeypatch):
        import sys

        # Pretend the optional dependency is absent. The engine must fall
        # back cleanly rather than crashing the debate.
        monkeypatch.setitem(sys.modules, "ploidy.api_client", None)

        proto = _make_protocol(
            messages=[
                _msg("s1", DebatePhase.POSITION, "A"),
                _msg("s2", DebatePhase.POSITION, "B"),
            ],
        )
        engine = ConvergenceEngine(use_llm=True)
        result = await engine.analyze(proto)
        assert result.meta_analysis is None


class TestSynthesisRootCause:
    """``_build_synthesis`` renders the root cause line for each category."""

    def test_productive_disagreement_root_cause_appears_in_synthesis(self):
        from ploidy.convergence import ConvergencePoint

        engine = ConvergenceEngine()
        points = [
            ConvergencePoint(
                category="productive_disagreement",
                summary="migration timing",
                session_a_view="now",
                session_b_view="later",
                resolution=None,
                root_cause="Deep anchored on prior migration cost.",
            ),
        ]
        out = engine._build_synthesis(
            "Should we migrate?",
            {"s1": "now", "s2": "later"},
            points,
            session_roles={"s1": "Deep", "s2": "Fresh"},
        )
        assert "Productive Disagreements" in out
        assert "Deep anchored on prior migration cost." in out

    def test_irreducible_root_cause_appears_in_synthesis(self):
        from ploidy.convergence import ConvergencePoint

        engine = ConvergenceEngine()
        points = [
            ConvergencePoint(
                category="irreducible",
                summary="latency vs safety",
                session_a_view="safety first",
                session_b_view="latency first",
                resolution=None,
                root_cause="Conflicting values: reliability vs performance.",
            ),
        ]
        out = engine._build_synthesis(
            "What matters more?",
            {"s1": "safety", "s2": "latency"},
            points,
        )
        assert "Irreducible Disagreements" in out
        assert "Conflicting values: reliability vs performance." in out
