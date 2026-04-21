# Ploidy as a Claude.ai Custom Connector

Goal: register Ploidy as a connector so users in the Claude.ai web / mobile
app can call `debate(...)` without installing Claude Code, and see the
answer-first `rendered_markdown` payload with the collapsed transcript
sections inline.

## Prerequisites

- A deployed Ploidy instance reachable over public HTTPS. The shortest
  recipe is [fly.io](../deploy/fly/README.md); the Helm chart at
  [`deploy/helm/ploidy`](../deploy/helm/) works for anyone already on
  kubernetes. Bare `docker compose` works if you terminate TLS in
  front (Caddy / Traefik / nginx).
- A Ploidy tenant token (`PLOIDY_TOKENS`). The deploy recipes show how
  to mint one with `openssl rand -hex 24`.
- (Optional) `PLOIDY_API_KEY` etc. if you want `mode="auto"` to work.

## Registration

Claude.ai → Settings → **Connectors** → **Add custom connector**.

| Field | Value |
|---|---|
| Name | **Ploidy** |
| Description | *Cross-session multi-agent debate with collapsed transcripts.* |
| URL | `https://<your-deploy>/mcp` |
| Authentication | **Bearer token** — the value from `PLOIDY_TOKENS` |

Save. Claude.ai fetches `tools/list` and registers every tool your
Ploidy server exposes.

## Recommended: surface only `debate`

The connector surface matters for discoverability — showing all 13
tools makes the UI look busy and encourages the LLM to pick the wrong
one. Two options:

1. **Hide legacy tools in the connector UI.** Claude.ai lets you toggle
   individual tools on/off; only enable `debate`.
2. **Deploy a lean surface.** Set `PLOIDY_HIDE_LEGACY_TOOLS=1` on the
   server (if supported in your Ploidy version — tracked as a future
   env flag) or fork the tool list in `server.py`.

Option 1 is zero-code and recommended for a prototype.

## Verifying end-to-end

In the Claude.ai chat, ask:

> Use Ploidy to debate: should we deprecate the 12 legacy tools in v0.5?

Expected output shape (rendered from `rendered_markdown`):

```markdown
## Ploidy debate result

**Confidence: 68%** · ✅ 2 · 🟡 1 · 🔴 0

▸ Synthesis
▸ Full transcript
▸ Meta-analysis    (only if PLOIDY_LLM_CONVERGENCE=1)

---
mode: `auto` · debate_id: `…`
```

Clicking the collapsed sections expands them inline. That's the UX.

## Live progress via SSE

The MCP tool call is a request/response — Claude waits until the full
debate converges, which feels slow. For a web-UI experience with live
phase-by-phase progress, hit the HTTP-only streaming route directly:

```
POST https://<your-deploy>/v1/debate/stream
Authorization: Bearer <token>
Content-Type: application/json

{"prompt": "...", "deep_n": 1, "fresh_n": 1}
```

Response is `text/event-stream` with frames typed
`phase_started` / `positions_generated` / `challenges_generated` /
`result` / `error`. A 30-line HTML page with `EventSource` is enough
to render a Grok-Heavy-style progress UI on top.

## Pre-launch checklist

Before opening the connector to a wider audience:

- [ ] `PLOIDY_RETENTION_DAYS` set so SQLite does not grow unbounded.
- [ ] Per-tenant rate limit via `PLOIDY_RATE_CAPACITY` /
      `PLOIDY_RATE_PER_SEC`.
- [ ] `/metrics` endpoint is not publicly reachable (proxy or
      firewall it).
- [ ] `PLOIDY_DASH_TOKEN` set so the dashboard is not world-readable.
- [ ] Tenant tokens rotated from the development defaults.
- [ ] Backups of `$PLOIDY_DB_PATH` (for fly.io: `flyctl volumes
      snapshot create`).

## When the Connector Registry approves

If Anthropic's Connector Registry eventually lists Ploidy, the per-user
setup collapses to one click. Until then, the Custom Connector path
above is the fastest way to put it in front of real users.
