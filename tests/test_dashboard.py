import json as _json

from ploidy import dashboard
from ploidy.store import DebateStore


def test_render_debate_list_escapes_prompt_and_id():
    html = dashboard._render_debate_list(
        [
            {
                "id": 'abc"><script>alert(1)</script>',
                "prompt": "<img src=x onerror=alert(1)>",
                "status": "active",
                "created_at": "2026-03-19",
            }
        ]
    )

    assert "<script>alert(1)</script>" not in html
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_render_debate_detail_escapes_transcript_and_synthesis():
    html = dashboard._render_debate_detail(
        {
            "id": "d1",
            "prompt": "<b>prompt</b>",
            "status": "complete",
            "created_at": "2026-03-19",
            "sessions": [{"id": "s1", "role": "experienced"}],
            "messages": [
                {
                    "session_id": "s1",
                    "phase": "position",
                    "content": '<script>alert("x")</script>',
                    "action": 'challenge" onclick="alert(1)',
                    "timestamp": "2026-03-19T00:00:00Z",
                }
            ],
            "convergence": {
                "confidence": 0.5,
                "points_json": '[{"category":"agreement","summary":"<svg onload=alert(1)>"}]',
                "synthesis": "<iframe></iframe>",
                "created_at": "2026-03-19",
            },
        }
    )

    assert '<script>alert("x")</script>' not in html
    assert "<iframe></iframe>" not in html
    assert "<svg onload=alert(1)>" not in html
    assert "&lt;b&gt;prompt&lt;/b&gt;" in html
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in html
    assert "&lt;iframe&gt;&lt;/iframe&gt;" in html


async def test_app_error_handler_does_not_crash_on_db_failure(monkeypatch, tmp_path):
    """Regression: html-module shadowing in app() crashed the 500 path.

    Pointing the dashboard at a nonexistent DB used to raise
    UnboundLocalError inside the except handler instead of returning 500.
    """
    monkeypatch.setenv("PLOIDY_DB_PATH", str(tmp_path / "missing" / "ploidy.db"))

    captured: list[dict] = []

    async def receive() -> dict:
        return {}

    async def send(msg: dict) -> None:
        captured.append(msg)

    scope = {"type": "http", "path": "/", "method": "GET"}
    await dashboard.app(scope, receive, send)

    starts = [m for m in captured if m["type"] == "http.response.start"]
    assert starts, "no response.start emitted"
    assert starts[0]["status"] == 500


# ---------------------------------------------------------------------------
# Auth, DB fetch, response-builder, and full-route coverage.
# ---------------------------------------------------------------------------


def _scope(path: str = "/", method: str = "GET", headers=None, client=("127.0.0.1", 1234)):
    return {
        "type": "http",
        "path": path,
        "method": method,
        "headers": headers or [],
        "client": client,
    }


async def _seed_dashboard_db(db_path):
    s = DebateStore(db_path=db_path)
    await s.initialize()
    try:
        await s.save_debate("dash01", "Prompt A")
        await s.update_debate_status("dash01", "complete")
        await s.save_session("dash01-deep-1", "dash01", "deep", "Prompt A")
        await s.save_message("dash01", "dash01-deep-1", "position", "Pos text")
        await s.save_convergence(
            "dash01",
            synthesis="Synth text",
            confidence=0.7,
            points_json='[{"category":"agreement","summary":"yes"}]',
        )
        await s.save_debate("dash02", "Prompt B")  # leave active
    finally:
        await s.close()


class TestAuthorization:
    def test_loopback_without_token_is_authorized(self, monkeypatch):
        monkeypatch.setattr(dashboard, "_DASH_TOKEN", None)
        assert dashboard._is_authorized(_scope(client=("127.0.0.1", 1))) is True
        assert dashboard._is_authorized(_scope(client=("::1", 1))) is True

    def test_non_loopback_without_token_is_rejected(self, monkeypatch):
        monkeypatch.setattr(dashboard, "_DASH_TOKEN", None)
        monkeypatch.setattr(dashboard, "_DASH_HOST", "0.0.0.0")
        assert dashboard._is_authorized(_scope(client=("10.0.0.5", 1))) is False

    def test_valid_bearer_token_is_authorized(self, monkeypatch):
        monkeypatch.setattr(dashboard, "_DASH_TOKEN", "secret123")
        headers = [(b"authorization", b"Bearer secret123")]
        assert dashboard._is_authorized(_scope(headers=headers)) is True

    def test_wrong_bearer_token_is_rejected(self, monkeypatch):
        monkeypatch.setattr(dashboard, "_DASH_TOKEN", "secret123")
        headers = [(b"authorization", b"Bearer wrong")]
        assert dashboard._is_authorized(_scope(headers=headers)) is False

    def test_missing_authorization_header_with_token_configured_is_rejected(self, monkeypatch):
        monkeypatch.setattr(dashboard, "_DASH_TOKEN", "secret123")
        assert dashboard._is_authorized(_scope(headers=[])) is False

    def test_non_bearer_scheme_is_rejected(self, monkeypatch):
        monkeypatch.setattr(dashboard, "_DASH_TOKEN", "secret123")
        headers = [(b"authorization", b"Basic Zm9vOmJhcg==")]
        assert dashboard._is_authorized(_scope(headers=headers)) is False


class TestDbFetch:
    async def test_fetch_debates_returns_seeded_rows(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        rows = await dashboard._fetch_debates()
        ids = {r["id"] for r in rows}
        assert {"dash01", "dash02"} <= ids

    async def test_fetch_debate_detail_joins_all_tables(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        detail = await dashboard._fetch_debate_detail("dash01")
        assert detail is not None
        assert detail["prompt"] == "Prompt A"
        assert len(detail["sessions"]) == 1
        assert len(detail["messages"]) == 1
        assert detail["convergence"]["synthesis"] == "Synth text"

    async def test_fetch_debate_detail_missing_id_returns_none(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)
        assert await dashboard._fetch_debate_detail("nonexistent") is None

    async def test_fetch_stats_counts_debates_and_computes_avg(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        stats = await dashboard._fetch_stats()
        assert stats["total_debates"] == 2
        assert stats["completed"] == 1
        assert stats["active"] == 1
        assert stats["avg_confidence"] == 0.7
        assert stats["total_messages"] == 1
        assert stats["total_sessions"] == 1


class TestResponseBuilders:
    async def test_send_response_emits_start_then_body(self):
        captured: list[dict] = []

        async def send(msg: dict) -> None:
            captured.append(msg)

        await dashboard._send_response(send, 200, "<p>hi</p>")
        assert captured[0]["type"] == "http.response.start"
        assert captured[0]["status"] == 200
        assert captured[1]["body"] == b"<p>hi</p>"

    async def test_send_json_serialises_data(self):
        captured: list[dict] = []

        async def send(msg: dict) -> None:
            captured.append(msg)

        await dashboard._send_json(send, 200, {"k": "v", "n": 3})
        body = captured[1]["body"].decode()
        assert _json.loads(body) == {"k": "v", "n": 3}


class TestAppRoutes:
    async def test_method_not_get_returns_405(self):
        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app(_scope(method="POST"), receive, send)
        assert captured[0]["status"] == 405

    async def test_unauthorized_without_token_on_non_loopback(self, monkeypatch):
        monkeypatch.setattr(dashboard, "_DASH_TOKEN", None)
        monkeypatch.setattr(dashboard, "_DASH_HOST", "0.0.0.0")

        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app(_scope(client=("10.0.0.5", 1)), receive, send)
        starts = [m for m in captured if m["type"] == "http.response.start"]
        assert starts[0]["status"] == 401

    async def test_list_route_returns_200_with_seeded_db(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app(_scope(path="/"), receive, send)
        starts = [m for m in captured if m["type"] == "http.response.start"]
        assert starts[0]["status"] == 200

    async def test_debate_detail_missing_returns_404(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app(_scope(path="/debate/nope"), receive, send)
        starts = [m for m in captured if m["type"] == "http.response.start"]
        assert starts[0]["status"] == 404

    async def test_api_debates_returns_json(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app(_scope(path="/api/debates"), receive, send)
        starts = [m for m in captured if m["type"] == "http.response.start"]
        assert starts[0]["status"] == 200
        # JSON route sets application/json content-type.
        headers = dict(starts[0]["headers"])
        assert headers[b"content-type"] == b"application/json"
        body = next(m["body"] for m in captured if m["type"] == "http.response.body")
        data = _json.loads(body)
        assert any(r["id"] == "dash01" for r in data)

    async def test_api_stats_returns_json(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app(_scope(path="/api/stats"), receive, send)
        starts = [m for m in captured if m["type"] == "http.response.start"]
        assert starts[0]["status"] == 200

    async def test_unknown_path_returns_404(self, tmp_path, monkeypatch):
        db = tmp_path / "dash.db"
        monkeypatch.setenv("PLOIDY_DB_PATH", str(db))
        await _seed_dashboard_db(db)

        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app(_scope(path="/does-not-exist"), receive, send)
        starts = [m for m in captured if m["type"] == "http.response.start"]
        assert starts[0]["status"] == 404

    async def test_non_http_scope_is_ignored(self):
        captured: list[dict] = []

        async def receive():
            return {}

        async def send(msg):
            captured.append(msg)

        await dashboard.app({"type": "websocket"}, receive, send)
        assert captured == []
