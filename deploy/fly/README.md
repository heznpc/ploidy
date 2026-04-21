# Deploying Ploidy on fly.io as a Claude.ai Custom Connector

This is the shortest path from repo → a Ploidy instance Claude.ai
can actually talk to. fly.io was picked because it ships free-tier
HTTPS, takes our existing Dockerfile unchanged, and scales to zero
when idle — so a prototype connector costs $0 until it's used.

## One-time setup

Install [`flyctl`](https://fly.io/docs/flyctl/install/) and sign in:

```sh
brew install flyctl
flyctl auth signup    # or auth login
```

## Deploy

From the repo root:

```sh
# 1. Rename the app (must be globally unique).
sed -i '' 's/ploidy-demo/<your-app-name>/' deploy/fly/fly.toml

# 2. Launch without re-running detection.
flyctl launch --no-deploy --copy-config --config deploy/fly/fly.toml

# 3. Mint a tenant token and set it as a secret.
export PLOIDY_DEMO_TOKEN=$(openssl rand -hex 24)
flyctl secrets set \
    PLOIDY_TOKENS="{\"$PLOIDY_DEMO_TOKEN\": \"my-tenant\"}" \
    PLOIDY_DASH_TOKEN="$(openssl rand -hex 16)"

# 4. (Optional) configure the OpenAI-compatible backend for mode="auto".
flyctl secrets set \
    PLOIDY_API_BASE_URL="https://api.anthropic.com/v1/openai" \
    PLOIDY_API_KEY="sk-ant-..." \
    PLOIDY_API_MODEL="claude-opus-4-6"

# 5. Ship it.
flyctl deploy --config deploy/fly/fly.toml
```

After deploy, the machine is reachable at
`https://<your-app-name>.fly.dev`. Smoke-test the health probe:

```sh
curl -s https://<your-app-name>.fly.dev/healthz
# {"status":"ok"}
```

## Register as a Custom Connector in Claude.ai

1. Claude.ai → Settings → **Connectors** → **Add custom connector**.
2. Fields:
   - **Name**: Ploidy
   - **URL**: `https://<your-app-name>.fly.dev/mcp`
   - **Authentication**: `Bearer` · value = `$PLOIDY_DEMO_TOKEN`
3. Save. Claude.ai will fetch `tools/list` and expose `debate` (plus the
   legacy 12 tools). You can hide legacy tools in the connector UI if
   you want a one-tool surface.

## Verify from curl

```sh
curl -N \
  -H "Authorization: Bearer $PLOIDY_DEMO_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST https://<your-app-name>.fly.dev/v1/debate/stream \
  -d '{
        "prompt": "monorepo or polyrepo for 3 teams, 12 microservices?",
        "deep_n": 1,
        "fresh_n": 1
      }'
```

Watch the `event: phase_started` / `positions_generated` /
`challenges_generated` / `result` frames arrive live.

## Day-2 operations

- **Logs**: `flyctl logs --config deploy/fly/fly.toml`.
- **Metrics**: scrape `https://<app>.fly.dev/metrics` — it's unauthenticated
  by design; put it behind a proxy or a Grafana Cloud scraper with
  basic auth if you expose the app publicly.
- **Retention**: `flyctl secrets set PLOIDY_RETENTION_DAYS=30` flips on
  the background purge so SQLite does not grow unbounded.
- **Rotate a tenant token**: update `PLOIDY_TOKENS` via
  `flyctl secrets set …` and redeploy. Existing sessions keep working
  until their next reconnect.

## Tearing down

```sh
flyctl apps destroy <your-app-name> --yes
```
