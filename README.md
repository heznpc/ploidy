# Ploidy

**Same model, different context depths, better decisions.**

[![CI](https://github.com/heznpc/ploidy/actions/workflows/ci.yml/badge.svg)](https://github.com/heznpc/ploidy/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-heznpc.github.io%2Fploidy-blue)](https://heznpc.github.io/ploidy/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)

Ploidy is an MCP server that orchestrates structured debates between multiple sessions of the same AI model — each with intentionally different context depths. When two sessions of the same model disagree, the cause is clear: one has context the other doesn't. That's a signal you can act on.

## Quick Start

```bash
# Install
pip install ploidy

# Start the server
python -m ploidy
```

**Terminal 1 (Deep session)** — tell your AI:
> "Start a Ploidy debate: Should we use monorepo or polyrepo?"

**Terminal 2 (Fresh session)** — tell your AI:
> "Join Ploidy debate a1b2c3d4e5f6"

The Deep session has your full project context. The Fresh session starts clean. They debate through a structured protocol, and the disagreements are interpretable because context is the only variable.

### MCP Client Configuration

```json
{
  "mcpServers": {
    "ploidy": {
      "type": "streamable-http",
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

## How It Works

```
Terminal 1 (Deep)              Terminal 2 (Fresh)
[Full project context]         [Zero context]
        |                              |
        └──── debate/start ──→ Ploidy Server ←── debate/join ────┘
                               (port 8765)
              position ──────→ [SQLite + WAL] ←────── position
              challenge ─────→ [State Machine] ←───── challenge
              converge ──────→ [Convergence]  ←────── converge
                                    ↓
                            Structured Result
                         (agreements, disagreements,
                          confidence score)
```

## Tools

| Tool | Description |
|------|-------------|
| `debate_start` | Begin a debate with a prompt |
| `debate_join` | Join as a fresh (zero-context) session |
| `debate_position` | Submit your stance |
| `debate_challenge` | Critique with semantic actions (agree/challenge/propose_alternative/synthesize) |
| `debate_converge` | Trigger convergence analysis |
| `debate_status` | Check current state |
| `debate_cancel` | Cancel in progress |
| `debate_delete` | Permanently delete |
| `debate_history` | List past debates |

## Configuration

All via environment variables:

```bash
PLOIDY_PORT=8765              # Server port
PLOIDY_DB_PATH=~/.ploidy/ploidy.db  # Database location
PLOIDY_LOG_LEVEL=INFO         # Logging level
PLOIDY_AUTH_TOKEN=secret      # Bearer token auth (optional)
```

## Docker

```bash
docker compose up
```

## Documentation

- [Getting Started](https://heznpc.github.io/ploidy/getting-started/) — Install and first debate
- [How It Works](https://heznpc.github.io/ploidy/how-it-works/) — Core concept
- [Architecture](https://heznpc.github.io/ploidy/architecture/) — Technical overview
- [API Reference](https://heznpc.github.io/ploidy/api-reference/) — Tool documentation
- [Research](https://heznpc.github.io/ploidy/research/) — Academic positioning

## Research

Ploidy extends Cross-Context Review ([Song 2026](https://arxiv.org/abs/2603.12123)) from unidirectional fresh-session review to bidirectional structured debate. The intersection of context asymmetry × same-model debate × structured protocol has zero published papers as of March 2026.

## License

MIT
