# Diploid

**Same model, different context, better decisions.**

---

## What is Diploid?

Diploid is an MCP (Model Context Protocol) server that orchestrates **cross-session multi-agent debate** between two instances of the same model. The key insight: you don't need different models to get meaningful disagreement -- you need **different context**.

Two sessions of the same model, given intentionally asymmetric context, will reason differently. One carries the full history -- prior decisions, accumulated assumptions, institutional knowledge. The other starts fresh -- unburdened by sunk costs, free from anchoring bias, able to question what the first takes for granted.

Diploid structures this disagreement into a convergence protocol, producing decisions that are stronger than either session could reach alone.

## The Core Concept: Context Asymmetry

Traditional multi-agent debate (MAD) pits different models against each other. But model differences are noisy -- you can't isolate *why* they disagree. Is it training data? Architecture? RLHF tuning?

Diploid takes a different approach:

- **Same model** -- eliminates model-level confounds
- **Different context** -- the *only* variable is what each session knows
- **Structured debate** -- not free-form argument, but a convergence protocol with defined phases

This makes disagreements *interpretable*. When two sessions of the same model disagree, you know exactly why: one has context the other doesn't. That's a signal, not noise.

## Etymology

In biology, **diploid** cells carry two complete sets of chromosomes -- one from each parent. Neither set is "better"; the organism needs both. One set carries the accumulated adaptations of one lineage, the other brings different adaptations. Together, they create genetic diversity that makes the organism more resilient.

Diploid the project works the same way:

- **Session A** (the experienced parent) -- carries full project context, prior decisions, learned patterns. It has wisdom, but also accumulated bias.
- **Session B** (the fresh parent) -- enters with minimal context, asks naive questions, challenges assumptions. It lacks experience, but also lacks anchoring.

Like different generations having a conversation: the experienced generation has hard-won knowledge but can't see past its own assumptions. The fresh generation asks "but why?" -- and sometimes that question is worth more than the answer.

## How It Works

1. **Session A** accumulates context naturally over a project's lifetime
2. When a decision point is reached, Diploid **spawns Session B** with deliberately limited context
3. Both sessions are given the same decision prompt
4. They enter a **structured debate protocol**:
   - Independent analysis (no cross-contamination)
   - Position statement (each declares their stance)
   - Challenge round (each critiques the other's position)
   - Convergence (find common ground or articulate irreducible disagreement)
5. The **convergence engine** synthesizes the result
6. Everything is persisted for future context

## Status

**Early development.** The architecture is defined, implementation is in progress.

## Key References

- [Knowledge Divergence in LLM Multi-Agent Debate](https://arxiv.org/abs/2603.05293) -- Analysis of how knowledge asymmetry affects debate dynamics
- [Bias Reinforcement in Multi-Agent Debate](https://arxiv.org/abs/2503.16814) -- Why naive MAD can amplify rather than correct biases (and how structured protocols help)

## License

MIT
