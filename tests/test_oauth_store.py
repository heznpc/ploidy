"""Tests for the OAuth 2.0 storage slice on ``DebateStore``.

Covers the three tables added for OAuth (clients / codes / tokens) plus
the retention hook. The provider layer sits on top of these and lands in
a follow-up PR.
"""

import pytest

from ploidy.store import DebateStore


@pytest.fixture
async def store(tmp_path):
    s = DebateStore(db_path=tmp_path / "oauth.db")
    await s.initialize()
    yield s
    await s.close()


async def _register_client(store: DebateStore, client_id: str = "cli-1") -> None:
    await store.save_oauth_client(
        client_id,
        redirect_uris=["https://claude.ai/api/mcp/auth_callback"],
        grant_types=["authorization_code", "refresh_token"],
        token_endpoint_auth_method="none",
        client_name="Test Client",
    )


class TestOauthClient:
    async def test_save_then_get_roundtrips_fields(self, store):
        await store.save_oauth_client(
            "c1",
            redirect_uris=["https://claude.ai/cb", "https://claude.com/cb"],
            grant_types=["authorization_code"],
            client_secret_hash="not-a-real-hash",
            token_endpoint_auth_method="client_secret_basic",
            client_name="MyApp",
        )
        row = await store.get_oauth_client("c1")
        assert row is not None
        assert row["client_id"] == "c1"
        assert row["redirect_uris"] == ["https://claude.ai/cb", "https://claude.com/cb"]
        assert row["grant_types"] == ["authorization_code"]
        assert row["token_endpoint_auth_method"] == "client_secret_basic"
        assert row["client_name"] == "MyApp"
        assert row["client_secret_hash"] == "not-a-real-hash"

    async def test_get_unknown_client_returns_none(self, store):
        assert await store.get_oauth_client("does-not-exist") is None


class TestOauthCode:
    async def test_save_then_consume_marks_single_use(self, store):
        await _register_client(store)
        await store.save_oauth_code(
            "code-xyz",
            client_id="cli-1",
            redirect_uri="https://claude.ai/api/mcp/auth_callback",
            scopes=["debate"],
            code_challenge="pkce-challenge-abc",
            code_challenge_method="S256",
            expires_at="2099-01-01 00:00:00",
        )
        first = await store.consume_oauth_code("code-xyz")
        assert first is not None
        assert first["client_id"] == "cli-1"
        assert first["scopes"] == ["debate"]
        assert first["code_challenge"] == "pkce-challenge-abc"
        # Second redemption must fail — single-use is load-bearing for PKCE.
        second = await store.consume_oauth_code("code-xyz")
        assert second is None

    async def test_consume_unknown_code_returns_none(self, store):
        assert await store.consume_oauth_code("nope") is None

    async def test_expired_code_cannot_be_consumed(self, store):
        await _register_client(store)
        await store.save_oauth_code(
            "code-old",
            client_id="cli-1",
            redirect_uri="https://claude.ai/api/mcp/auth_callback",
            scopes=["debate"],
            code_challenge="c",
            code_challenge_method="S256",
            expires_at="2020-01-01 00:00:00",
        )
        assert await store.consume_oauth_code("code-old") is None

    async def test_code_deleted_when_client_is_cascaded(self, store):
        # ON DELETE CASCADE makes sure dropping a client also evicts
        # any pending codes so an orphan code cannot redeem against a
        # different client that later reuses the id.
        await _register_client(store)
        await store.save_oauth_code(
            "code-cascade",
            client_id="cli-1",
            redirect_uri="https://claude.ai/api/mcp/auth_callback",
            scopes=["debate"],
            code_challenge="c",
            code_challenge_method="S256",
            expires_at="2099-01-01 00:00:00",
        )
        db = store._db
        await db.execute("DELETE FROM oauth_clients WHERE client_id = 'cli-1'")
        await db.commit()
        assert await store.consume_oauth_code("code-cascade") is None


class TestOauthToken:
    async def test_save_and_resolve_access_token(self, store):
        await _register_client(store)
        await store.save_oauth_token(
            "acc-1",
            kind="access",
            client_id="cli-1",
            scopes=["debate"],
            expires_at="2099-01-01 00:00:00",
        )
        row = await store.get_oauth_token("acc-1")
        assert row is not None
        assert row["kind"] == "access"
        assert row["client_id"] == "cli-1"
        assert row["scopes"] == ["debate"]

    async def test_unknown_token_returns_none(self, store):
        assert await store.get_oauth_token("never-issued") is None

    async def test_expired_token_is_not_returned(self, store):
        await _register_client(store)
        await store.save_oauth_token(
            "acc-expired",
            kind="access",
            client_id="cli-1",
            scopes=["debate"],
            expires_at="2020-01-01 00:00:00",
        )
        assert await store.get_oauth_token("acc-expired") is None

    async def test_revoked_token_is_not_returned(self, store):
        await _register_client(store)
        await store.save_oauth_token(
            "acc-live",
            kind="access",
            client_id="cli-1",
            scopes=["debate"],
            expires_at="2099-01-01 00:00:00",
        )
        await store.revoke_oauth_token("acc-live")
        assert await store.get_oauth_token("acc-live") is None

    async def test_refresh_tokens_survive_without_expiry(self, store):
        # Refresh tokens are typically long-lived — the schema permits
        # a NULL expires_at so get_oauth_token must not require one.
        await _register_client(store)
        await store.save_oauth_token(
            "ref-1",
            kind="refresh",
            client_id="cli-1",
            scopes=["debate"],
            expires_at=None,
        )
        row = await store.get_oauth_token("ref-1")
        assert row is not None
        assert row["kind"] == "refresh"

    async def test_revoke_unknown_token_is_silent_noop(self, store):
        # Idempotence: operators must be able to retry revocation on a
        # flaky network without the call turning into an error.
        await store.revoke_oauth_token("never-existed")


class TestOauthRetention:
    async def test_purge_removes_used_and_expired_rows(self, store):
        await _register_client(store)
        # Expired code.
        await store.save_oauth_code(
            "code-expired",
            client_id="cli-1",
            redirect_uri="https://claude.ai/api/mcp/auth_callback",
            scopes=["debate"],
            code_challenge="c",
            code_challenge_method="S256",
            expires_at="2020-01-01 00:00:00",
        )
        # Consumed code (used=1).
        await store.save_oauth_code(
            "code-used",
            client_id="cli-1",
            redirect_uri="https://claude.ai/api/mcp/auth_callback",
            scopes=["debate"],
            code_challenge="c",
            code_challenge_method="S256",
            expires_at="2099-01-01 00:00:00",
        )
        await store.consume_oauth_code("code-used")
        # Live code — must survive the purge.
        await store.save_oauth_code(
            "code-live",
            client_id="cli-1",
            redirect_uri="https://claude.ai/api/mcp/auth_callback",
            scopes=["debate"],
            code_challenge="c",
            code_challenge_method="S256",
            expires_at="2099-01-01 00:00:00",
        )
        # Expired token.
        await store.save_oauth_token(
            "tok-old",
            kind="access",
            client_id="cli-1",
            scopes=["debate"],
            expires_at="2020-01-01 00:00:00",
        )
        # Revoked token.
        await store.save_oauth_token(
            "tok-revoked",
            kind="access",
            client_id="cli-1",
            scopes=["debate"],
            expires_at="2099-01-01 00:00:00",
        )
        await store.revoke_oauth_token("tok-revoked")
        # Live token — must survive.
        await store.save_oauth_token(
            "tok-live",
            kind="access",
            client_id="cli-1",
            scopes=["debate"],
            expires_at="2099-01-01 00:00:00",
        )

        removed = await store.purge_oauth_expired()
        # 2 codes + 2 tokens = 4 rows removed. The live code and live
        # token must remain readable.
        assert removed == 4
        assert await store.consume_oauth_code("code-live") is not None
        assert await store.get_oauth_token("tok-live") is not None
