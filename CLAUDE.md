# Diploid

Cross-session multi-agent debate MCP server.

## Language & Runtime
- Python 3.11+
- Async-first (asyncio, aiosqlite)
- MCP server using the `mcp` Python SDK

## Core Concept
Context asymmetry is a feature, not a bug. Two sessions of the same model with different context produce meaningful, interpretable disagreement.

## Architecture
- `server.py` -- MCP server entry point, exposes debate tools
- `protocol.py` -- Debate protocol definitions (phases, transitions, rules)
- `session.py` -- Session lifecycle management, context injection
- `convergence.py` -- Convergence engine, synthesis logic
- `store.py` -- Persistence layer (aiosqlite), debate history

## Conventions
- Format with `ruff`
- Test with `pytest` (async tests via `pytest-asyncio`)
- All public functions need docstrings
- Type hints on all function signatures
