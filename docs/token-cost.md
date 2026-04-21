# Token cost and how to keep it down

Ploidy calls the API multiple times per debate, so it is naturally
more expensive than a single chat turn. The good news is every knob
that drives that cost is exposed. This page walks through each one
and tells you which default to keep, which to tune, and which to
ignore unless you are doing research.

## Cost baseline (what you'd spend if every call was a single Q&A)

Each `debate(mode='auto')` run fires these LLM calls:

1. Deep position generation
2. Fresh position generation
3. Challenge from Deep → Fresh
4. Challenge from Fresh → Deep
5. (optional) LLM-backed convergence meta-analysis when
   `PLOIDY_LLM_CONVERGENCE=1`

At effort=high the per-call output ceiling is 4096 tokens. Typical
1×1 auto debate without context_documents burns roughly:

| | Input tokens | Output tokens |
|---|---|---|
| Per call | ~600 – 1,200 | ~2,000 – 4,000 |
| Debate total (×4 calls) | ~3,000 – 5,000 | ~8,000 – 16,000 |

Scale that against your model's pricing and you get the honest number.
With Opus 4.6 it lands around **$0.70 – $1.50 per debate**. With Sonnet
4.6, **$0.15 – $0.30**. Context_documents linearly grow the input
column.

## Knobs that save meaningful money

### 1. Prompt caching (free when enabled)

The two challenge calls quote the *same* pair of positions. v0.4.1
onwards ships them as a byte-stable shared prefix, which every major
provider now caches automatically.

For Anthropic (where caching gives the biggest discount) flip on
**`PLOIDY_API_CACHE=1`** so Ploidy passes explicit
`cache_control: {"type": "ephemeral"}` on the shared prefix. That
tells the server to treat the positions block as a 5-minute cache
segment — the second challenge hits cache at ~10% input-token cost.

- Works automatically when `PLOIDY_API_BASE_URL` points at
  `*.anthropic.com`. Other providers see the same byte-stable prefix
  and fall back to their automatic prefix cache (OpenAI, DeepSeek,
  Together — all supported as of 2026-04).
- Savings on a 1×1 run: roughly **30-40% of total input tokens**.
- Zero risk — cached responses are not reused, only cached *prompt
  prefix tokens* are discounted on the next call.

### 2. Model choice per side

`debate(deep_model=..., fresh_model=...)` takes per-side overrides.
In practice the deep side benefits most from top-tier reasoning; the
fresh side and the challenges are perfectly served by a mid-tier
model.

- Example split: `deep_model="claude-opus-4-6"`,
  `fresh_model="claude-sonnet-4-6"`.
- Saves roughly **40-50% of combined spend** on a 1×1 auto debate
  with very little observable quality drop.

### 3. Effort level

`effort` maps directly to the per-call output ceiling:

| effort | `max_tokens` |
|---|---|
| `"low"` | 1024 |
| `"medium"` | 2048 |
| `"high"` (default) | 4096 |
| `"max"` | 8192 |

Output tokens are the expensive side of the bill. Dropping from
`"high"` to `"medium"` roughly **halves output spend** and only
affects how verbose each response is — the structure (positions,
challenges, convergence categories) is unchanged.

### 4. Context budget cap

`PLOIDY_MAX_CONTEXT_TOKENS` rejects any run whose combined
`context_documents` exceed the ceiling. It is a spend guardrail, not
a soft trim — the caller gets a `ProtocolError` telling them what to
shrink. The service defaults to no cap (research behaviour); production
deployments should set something like `20000` so a stray huge-context
debate cannot silently bill $50.

### 5. `mode="solo"` when the caller already has both sides

If you are orchestrating from Claude Code and can write both
positions yourself (the `/ploidy` slash command does exactly this),
Ploidy's API spend is **zero**. Every convergence decision is made
by the rule-based engine over the submitted text. Turn on
`PLOIDY_LLM_CONVERGENCE=1` only when the meta-analysis narrative is
worth one extra call.

### 6. Rate limit per tenant

`PLOIDY_RATE_CAPACITY` / `PLOIDY_RATE_PER_SEC` are a hard cap on how
many debates any single tenant can start in a burst / per second.
Default off. Set something like capacity=10, rate=0.05 to make sure a
misbehaving integration cannot run 500 parallel Opus debates on your
card.

## Knobs that do not save much (skip unless curious)

- `context_pct` — percentage of `context_documents` to keep. Nice for
  research sweeps on context-length sensitivity; in production you
  want the real context or nothing, so you rarely set it.
- `injection_mode` — where the context enters the prompt. Affects
  behaviour, not cost.
- `language` — prompts the model to answer in a specific language.
  Purely behavioural.

## Research-only knobs (big quality impact, big cost impact)

- `deep_n` / `fresh_n` — parallel positions per side. Each additional
  position is one more LLM call at the position phase. Set to 2+
  only when you need Stochastic-N isolation for experiments; for
  production `1×1` is correct.
- `effort="max"` — doubles output ceiling. Rarely worth the price
  outside evaluation runs.

## Recommended production defaults

```sh
PLOIDY_API_CACHE=1
PLOIDY_MAX_CONTEXT_TOKENS=20000
PLOIDY_RATE_CAPACITY=10
PLOIDY_RATE_PER_SEC=0.05
# Keep effort default at "high" for quality; drop to "medium" if
# tight-budget is the priority.
```

Combined effect vs the same workload with zero tuning: roughly
**55-65% cheaper** on Opus, **40-50% cheaper** on Sonnet.
