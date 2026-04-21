"""Tests for v0.4.1 token-saving changes.

Three things are verified here:

1. ``generate_challenge`` emits a byte-stable shared position block
   across both challenge calls of a debate — the precondition for
   prefix caching to work.
2. When ``PLOIDY_API_CACHE`` is set and the base URL points at
   Anthropic, the user message is a structured content list with a
   cache_control breakpoint on the shared prefix.
3. The service-level ``max_context_tokens`` ceiling rejects oversized
   ``context_documents`` before the API is ever called.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ploidy.service import DebateService
from ploidy.store import DebateStore


def _mock_completion(content: str = "ok"):
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.fixture
def _api_env(monkeypatch):
    monkeypatch.setenv("PLOIDY_API_BASE_URL", "https://api.anthropic.com/v1/openai")
    monkeypatch.setenv("PLOIDY_API_KEY", "test-key")


class TestChallengePrefixCaching:
    async def test_shared_prefix_is_byte_stable_across_roles(self, _api_env, monkeypatch):
        """Deep-side and fresh-side challenges ship the same position block."""
        from ploidy import api_client

        monkeypatch.setattr(api_client, "_API_BASE_URL", "https://api.anthropic.com/v1/openai")

        captured_messages: list[list[dict]] = []

        async def fake_create(**kwargs):
            captured_messages.append(kwargs["messages"])
            return _mock_completion("challenge text")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = fake_create

        with patch.object(api_client, "_get_client", return_value=mock_client):
            await api_client.generate_challenge(
                own_position="DEEP pos",
                other_position="FRESH pos",
                own_role="deep",
                other_role="fresh",
            )
            await api_client.generate_challenge(
                own_position="FRESH pos",
                other_position="DEEP pos",
                own_role="fresh",
                other_role="deep",
            )

        assert len(captured_messages) == 2
        prefix_a = _extract_prefix(captured_messages[0])
        prefix_b = _extract_prefix(captured_messages[1])
        assert prefix_a == prefix_b, "prefix must be byte-stable for caching to work"
        assert "**Deep session**" in prefix_a
        assert "**Fresh session**" in prefix_a

    async def test_cache_control_emitted_for_anthropic_when_enabled(self, _api_env, monkeypatch):
        from ploidy import api_client

        monkeypatch.setattr(api_client, "_API_BASE_URL", "https://api.anthropic.com/v1/openai")
        monkeypatch.setattr(api_client, "_CACHE_ENABLED", True)

        captured: list[list[dict]] = []

        async def fake_create(**kwargs):
            captured.append(kwargs["messages"])
            return _mock_completion("ok")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = fake_create

        with patch.object(api_client, "_get_client", return_value=mock_client):
            await api_client.generate_challenge(
                own_position="D",
                other_position="F",
                own_role="deep",
                other_role="fresh",
            )

        user_content = captured[0][-1]["content"]
        assert isinstance(user_content, list), "expected structured content for cache_control"
        # First block is the cacheable prefix with the control marker.
        assert user_content[0]["cache_control"] == {"type": "ephemeral"}
        # Second block is the role-specific tail without cache_control.
        assert "cache_control" not in user_content[1]

    async def test_no_cache_control_for_other_providers(self, monkeypatch):
        from ploidy import api_client

        monkeypatch.setattr(api_client, "_API_BASE_URL", "https://openrouter.ai/api/v1")
        monkeypatch.setattr(api_client, "_CACHE_ENABLED", True)

        captured: list[list[dict]] = []

        async def fake_create(**kwargs):
            captured.append(kwargs["messages"])
            return _mock_completion("ok")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = fake_create

        with patch.object(api_client, "_get_client", return_value=mock_client):
            await api_client.generate_challenge(
                own_position="D",
                other_position="F",
                own_role="deep",
                other_role="fresh",
            )

        user_content = captured[0][-1]["content"]
        # Non-Anthropic providers get a plain string — they still benefit
        # from byte-stable prefixes via automatic prefix caching, but
        # never see the explicit cache_control shape.
        assert isinstance(user_content, str)

    async def test_cache_disabled_falls_back_to_string(self, monkeypatch):
        from ploidy import api_client

        monkeypatch.setattr(api_client, "_API_BASE_URL", "https://api.anthropic.com/v1/openai")
        monkeypatch.setattr(api_client, "_CACHE_ENABLED", False)

        captured: list[list[dict]] = []

        async def fake_create(**kwargs):
            captured.append(kwargs["messages"])
            return _mock_completion("ok")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = fake_create

        with patch.object(api_client, "_get_client", return_value=mock_client):
            await api_client.generate_challenge(
                own_position="D",
                other_position="F",
                own_role="deep",
                other_role="fresh",
            )

        user_content = captured[0][-1]["content"]
        assert isinstance(user_content, str)


def _extract_prefix(messages: list[dict]) -> str:
    """Return the shared prefix from a captured user message."""
    content = messages[-1]["content"]
    if isinstance(content, list):
        return content[0]["text"]
    # For the plain-string path, the prefix is everything before the "---"
    # role-specific tail.
    return content.split("---", 1)[0]


class TestContextBudgetCap:
    async def test_cap_allows_within_budget(self, tmp_path):
        svc = DebateService(
            store=DebateStore(db_path=tmp_path / "b.db"),
            max_context_tokens=1000,
        )
        await svc.initialize()
        try:
            # ~100 tokens via the 4-chars-per-token approximation.
            result = await svc.start_debate("ok?", context_documents=["x" * 400])
            assert result["phase"] == "independent"
        finally:
            await svc.shutdown()

    async def test_cap_rejects_oversized_bundle(self, tmp_path):
        svc = DebateService(
            store=DebateStore(db_path=tmp_path / "b.db"),
            max_context_tokens=100,
        )
        await svc.initialize()
        try:
            with pytest.raises(Exception, match="exceeds configured ceiling"):
                await svc.start_debate("ok?", context_documents=["x" * 800])
        finally:
            await svc.shutdown()

    async def test_cap_disabled_by_default(self, tmp_path):
        """When max_context_tokens is None, any doc size is accepted."""
        svc = DebateService(store=DebateStore(db_path=tmp_path / "b.db"))
        await svc.initialize()
        try:
            # 10k chars without a cap should pass.
            result = await svc.start_debate("ok?", context_documents=["x" * 10000])
            assert result["phase"] == "independent"
        finally:
            await svc.shutdown()
