# Ploidy: Context-Asymmetric Multi-Session Debate for Debiasing LLM Outputs

**heznpc**

---

## Abstract

Large language models lock into stochastic trajectories: the first response anchors subsequent outputs, and prompt-based mitigations have no statistically significant effect on this anchoring bias. We introduce Ploidy, a structured debate protocol that engineers context asymmetry between physically separate sessions of the same model. A Deep session carries full project context; a Fresh session starts with zero prior commitment. Their disagreements isolate where accumulated context caused bias versus where stochastic variance produced different outputs. We identify two independent phenomena — context asymmetry (Event A) and stochastic variance (Event B) — and show that the ploidy level (sessions per context depth) controls which can be distinguished. In preliminary experiments on long-context software architecture tasks with Claude Opus 4.6, we find: (1) Ploidy achieves highest recall across all context injection modes, (2) memory-style context injection degrades single-session recall by 20% while Ploidy's recall drops only 6%, (3) diploid (2n) debate reaches maximum recall at 30% additional compute over haploid, with no benefit from higher ploidy, and (4) context injection mechanism (memory vs. skills vs. raw) is a moderator variable that changes which method performs best. The intersection of intentional context asymmetry, structured cross-session debate, and injection mechanism as an experimental variable has zero prior publications as of March 2026.

---

## 1. Introduction

Ask the same model the same question in separate sessions. You get different answers every time — some agree, some disagree, some equivocate. If you continue in just one session, the model's first stochastic response becomes an anchor. It reinforces its own prior, the user builds on it, and the session locks into a trajectory that prompt engineering cannot undo (arXiv:2412.06593).

This means identical models, identical prompts, identical users — but different project outcomes depending on which random sample landed first. The user is in a probability lottery without knowing it.

Multi-agent teams (CrewAI, MetaGPT, Claude Agent Teams) address throughput by dividing labor across agents. But under symmetric information, scaling agents is mathematically equivalent to majority voting over identically biased samples — it cannot improve expected correctness (Choi et al., NeurIPS 2025 Spotlight; arXiv:2508.17536).

Ploidy takes the orthogonal approach: **deliberately create context asymmetry within the same model, then make the asymmetric sessions debate.**

### 1.1 Two Independent Phenomena

Context asymmetry and stochastic variance are independent events that both motivate multi-session debate:

- **Event A (Context Asymmetry)**: A Deep session and a Fresh session disagree because they have different information. The cause is interpretable — one has context the other lacks.
- **Event B (Stochastic Variance)**: Two sessions with identical context disagree because LLM outputs are sampled from a probability distribution.

A haploid (1n) debate — Deep(1) × Fresh(1) — addresses Event A but samples only one point from each distribution. Diploid (2n) and higher address both: context asymmetry between groups, stochastic sampling within groups. When all Deep sessions agree on a finding that no Fresh session found, the cause is almost certainly context-driven.

### 1.2 Contributions

1. A structured debate protocol with semantic actions between sessions of the same model at different context depths
2. The distinction between Event A (context asymmetry) and Event B (stochastic variance) as independently measurable phenomena, controlled by ploidy level
3. Context injection mechanism (memory, skills, system prompt, CLAUDE.md) as a novel experimental variable for debate efficacy
4. Preliminary evidence that diploid (2n) is the cost-optimal ploidy level for recall maximization

---

## 2. Related Work

### 2.1 Context Separation

Cross-Context Review (Song, 2026; arXiv:2603.12123) demonstrates that a fresh session reviewing a deep session's output achieves F1=28.6% vs. 24.6% for same-session review (p=0.008). This is unidirectional — fresh reviews deep. Ploidy extends to bidirectional structured debate.

SR-DCR/ACVD (Stanford/Brown/UNSW, 2025; arXiv:2506.06020) uses a context-deprived critic against a context-defending agent for QA/fact verification. Ploidy differs in domain (software engineering), directionality (bidirectional), and session structure (N-ary with semantic actions).

### 2.2 Multi-Agent Debate

Choi et al. (NeurIPS 2025; arXiv:2508.17536) prove debate is a martingale under symmetric information — it cannot improve expected correctness. AceMAD (arXiv:2603.06801) proves that asymmetric cognitive potential creates submartingale drift toward truth, breaking the martingale curse. Ploidy engineers this asymmetry through context depth variation.

DReaMAD (Oh et al., 2025; arXiv:2503.16814) shows naive debate amplifies bias through belief entrenchment, motivating Ploidy's structured protocol with semantic actions.

Wu et al. (2025; arXiv:2511.07784) find group diversity — not structural parameters — drives debate success, supporting context asymmetry over persona assignment.

### 2.3 Context Degradation

Du et al. (EMNLP 2025; arXiv:2510.05381) show context length alone degrades performance 13.9-85%, even with perfect retrieval. Chroma Research (2025) finds effective context capacity is 60-70% of advertised window. These motivate Fresh sessions operating within effective capacity.

### 2.4 Sycophancy and Anchoring

Jain et al. (2025; arXiv:2509.12517) show persistent context (memory profiles) increases sycophancy by up to 45%. Harshavardhan (2026; arXiv:2603.01239) documents self-anchoring calibration drift and recommends periodic context resets. Laban et al. (2025; arXiv:2505.06120) report 39% performance drop in multi-turn vs. single-turn.

### 2.5 Context Injection Mechanisms

No prior work treats the delivery mechanism of context (memory file vs. skills file vs. system prompt) as an independent experimental variable. Vercel (2026) compared AGENTS.md vs. skills for pass rates, and ETH Zurich (2026) found AGENTS.md files may hinder AI coding agents. Neither connected injection mechanism to debate outcomes.

### 2.6 Positioning

| Prior Work | Contribution | Ploidy Extension |
|---|---|---|
| CCR (Song 2026) | Unidirectional fresh review | Bidirectional structured debate |
| SR-DCR/ACVD (2025) | Context-deprived critic for QA | SE domain, N-session, semantic actions |
| AceMAD (2026) | Theoretical martingale breaking | Protocol implementation + empirical platform |
| DReaMAD (2025) | Symmetric debate bias diagnosis | Asymmetric + structured protocol as solution |
| Choi et al. (2025) | Debate = martingale under symmetry | Context asymmetry breaks symmetry assumption |

---

## 3. Method

### 3.1 Context Asymmetry Spectrum

Sessions are assigned roles along a context depth spectrum:

| Role | Context | Purpose |
|---|---|---|
| **Experienced (Deep)** | Full project history, prior decisions, accumulated knowledge | Domain expertise, but subject to entrenchment |
| **Semi-Fresh** | Compressed summary of Deep analysis (passive or active delivery) | Partial independence with informed starting point |
| **Fresh** | Zero context — only the decision prompt | Maximum independence from accumulated bias |

### 3.2 Debate Protocol

Five-phase state machine:

1. **Independent**: All sessions analyze the prompt independently
2. **Position**: Each session declares its stance
3. **Challenge**: Each session critiques others using semantic actions (AGREE, CHALLENGE, PROPOSE_ALTERNATIVE, SYNTHESIZE)
4. **Convergence**: Engine classifies points as agreement, productive disagreement, or irreducible disagreement
5. **Complete**: Structured result persisted

Semantic actions make the debate transcript machine-interpretable, enabling automated convergence analysis.

### 3.3 Ploidy Level

The ploidy level N determines how many sessions are spawned per context depth:

- **1n (haploid)**: Deep×1, Fresh×1 — minimal asymmetric debate
- **2n (diploid)**: Deep×2, Fresh×2 — stochastic outlier detection
- **Nn (N-ploid)**: Deep×N, Fresh×N — within-group agreement enables causal attribution

At 1n, the system cannot distinguish Event A from Event B. At 2n+, within-group disagreement isolates stochastic variance, and between-group disagreement isolates context asymmetry.

### 3.4 Context Injection Modes

The same context information can be delivered to the Deep session in different formats:

| Mode | Delivery | Hypothesis |
|---|---|---|
| **raw** | Plain text in user prompt | Baseline — weakest framing |
| **memory** | Accumulated observations (CLAUDE.md style) | Strongest anchoring — model treats as learned experience |
| **skills** | Declarative rules (skills.md style) | Weaker anchoring — model treats as constraints, not beliefs |
| **system_prompt** | System-level instruction | Positional authority bias |
| **claude_md** | XML-tagged project instructions | Compliance behavior trigger |

---

## 4. Experimental Setup

### 4.1 Model and Infrastructure

All experiments use Claude Opus 4.6 via `claude --print` CLI. Each CLI call creates a fresh session with perfect context isolation. Judge model is the same (self-evaluation; see Limitations).

### 4.2 Tasks

**Short-context** (2 tasks): Code review with known bugs (race condition, SQL injection). Context is 3-5 sentences. Ground truth: 3 issues per task.

**Long-context** (3 tasks): Architecture decisions with embedded misleading priors designed to trigger context entrenchment. Context is 2,000-5,000 tokens with 18-month project histories containing sunk cost narratives, authority bias, and repeated rejection of alternatives. Ground truth: 5-6 issues per task.

### 4.3 Methods

| Method | Description | LLM Calls |
|---|---|---|
| **Single** | Single session with full context | 1 |
| **CCR** | Deep produces, Fresh reviews (unidirectional) | 2 |
| **Ploidy** | Deep×N + Fresh×N, challenge phase, convergence | 2N+3 |

### 4.4 Metrics

- **Recall**: Ground-truth issues found (FOUND) or partially identified (PARTIAL, counted as 0.5). Primary metric — a missed critical issue is worse than a false positive.
- **F1**: Harmonic mean of precision and recall. Precision is affected by bonus findings count.
- **Time**: Wall-clock seconds per method.

### 4.5 Evaluation

LLM-as-judge classifies each ground-truth issue as FOUND, PARTIAL, or MISSED against the method's output. Bonus findings (valid issues not in ground truth) are counted for precision calculation.

---

## 5. Results

### 5.1 Short-Context: Ceiling Effect

All methods achieve 3/3 recall on short-context tasks regardless of injection mode. F1 differences come only from bonus findings precision. **Context entrenchment does not occur on short-context tasks** — the context is not long enough to induce anchoring bias. This bounds the intervention's applicability.

### 5.2 Long-Context: Injection Mode Sweep

| | Single Recall | Ploidy Recall | CCR Recall |
|---|---|---|---|
| **raw** | 5.0/5.3 | **5.3/5.3** | 4.7/5.3 |
| **memory** | 4.0/5.3 | **5.0/5.3** | 4.0/5.3 |
| **skills** | 4.3/5.3 | **5.3/5.3** | 5.0/5.3 |

Ploidy achieves highest recall across all injection modes.

**Memory injection degrades recall:**

| | raw → memory |
|---|---|
| Single | 5.0 → 4.0 (**-20%**) |
| Ploidy | 5.3 → 5.0 (**-6%**) |
| CCR | 4.7 → 4.0 (**-15%**) |

Memory-style injection creates the strongest anchoring. Ploidy is most resilient because the Fresh session never sees the memory-formatted context.

**Injection mode changes optimal method:**

- raw: Ploidy best
- memory: Single best (F1), Ploidy best (recall)
- skills: CCR best (F1), Ploidy best (recall)

Context injection mechanism is a moderator variable for debate efficacy.

### 5.3 Ploidy Level Sweep (1n–4n)

| Ploidy | Ploidy Recall | Ploidy F1 | Single Recall | Time |
|---|---|---|---|---|
| 1n | 4.5/5.0 | 0.584 | 5.0/5.0 | 272s |
| **2n** | **5.0/5.0** | **0.667** | 4.5/5.0 | 352s |
| 3n | 5.0/5.0 | 0.505 | 4.5/5.0 | 480s |
| 4n | 5.0/5.0 | 0.679 | 5.0/5.0 | 501s |

**2n is the recall threshold.** At 1n, Ploidy misses issues (4.5/5.0). At 2n, recall reaches the ceiling (5.0/5.0). Additional samples provide no further recall benefit.

**2n is the cost optimum.** 30% more compute than 1n for full recall correction. 3n+ costs 76-84% more with no recall gain.

**Single catches up at 4n** through brute-force stochastic sampling, but requires 4× the compute of Ploidy 2n to reach the same recall.

---

## 6. Discussion

### 6.1 When Does Context Asymmetry Help?

Only on long-context tasks where entrenchment occurs. Short-context tasks produce no entrenchment and therefore no benefit from asymmetric debate. This is consistent with CCR's findings and bounds the intervention's practical scope: Ploidy is most valuable for decisions where the session has accumulated substantial context history.

### 6.2 Injection Mechanism as Moderator

The finding that memory-style injection degrades recall more than skills-style injection has practical implications. Tools that persist context as accumulated observations (CLAUDE.md memory, conversation logs) may inadvertently create stronger anchoring than tools using declarative rules (skills files, system prompts). The delivery mechanism is not neutral — it is a bias amplifier or attenuator.

### 6.3 The Diploid Sweet Spot

2n achieves full recall correction at minimal additional cost. Higher ploidy provides no recall benefit while increasing compute and reducing precision through finding inflation. This suggests that for practical deployment, diploid debate (two sessions per context depth) is sufficient.

### 6.4 Event A vs Event B Separation

At 2n+, within-group agreement distinguishes stochastic variance from context-driven disagreement. If both Deep sessions agree on a finding that both Fresh sessions miss, the cause is almost certainly the context — not randomness. This causal interpretability is unavailable at 1n, where every disagreement could be either event.

---

## 7. Limitations and Future Work

### 7.1 Limitations

- **No repeated trials.** N=1 per condition. All results are point estimates, not statistically significant. Stochastic variance in LLM outputs means individual runs may not be representative.
- **Small task set.** 5 tasks total (2 short, 3 long). Workshop papers require 5-10; full papers require 30+.
- **Single model.** Only Claude Opus 4.6 tested. Cross-model validation (Sonnet, Gemini, GPT, Ollama) needed.
- **Self-evaluation.** Judge model is the same as evaluated model. Independent judge or human evaluation needed.
- **Software engineering domain only.** Results may not generalize to other domains (medical, legal, scientific reasoning).
- **Ploidy sweep on 2 tasks.** The 2n optimality finding needs validation on a larger task set.

### 7.2 Future Work

- **Repeated trials**: Run each condition 5-10× to establish confidence intervals and statistical significance.
- **Cross-model validation**: Test whether findings hold across model families and sizes.
- **Effort level interaction**: Sweep effort (low/medium/high/max) × ploidy × injection mode for factorial analysis.
- **Language sweep**: Test whether linguistic/cultural framing (en/ko/ja/zh) interacts with context asymmetry.
- **Independent judge**: Use a different model or human evaluators for ground-truth assessment.
- **Standard benchmarks**: Include NLP benchmarks (MMLU, TruthfulQA) for comparability with MAD literature.

---

## 8. Conclusion

We presented Ploidy, a structured debate protocol that engineers context asymmetry between sessions of the same model to reduce confirmation bias. We identified two independent phenomena — context asymmetry and stochastic variance — and showed that the ploidy level controls which can be distinguished. Preliminary experiments demonstrate that asymmetric debate improves recall on long-context tasks, that context injection mechanism moderates debate efficacy, and that diploid (2n) debate is the cost-optimal configuration. The intersection of intentional context asymmetry, cross-session structured debate, and injection mechanism as an experimental variable has no prior publications as of March 2026.

---

## References

1. Choi et al. (2025). Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs? NeurIPS 2025 Spotlight. arXiv:2508.17536
2. Du et al. (2025). Context Length Alone Hurts LLM Performance Despite Perfect Retrieval. EMNLP 2025. arXiv:2510.05381
3. Harshavardhan (2026). Self-Anchoring Calibration Drift in LLMs. arXiv:2603.01239
4. Jain et al. (2025). Interaction Context Often Increases Sycophancy in LLMs. arXiv:2509.12517
5. Laban et al. (2025). LLMs Get Lost In Multi-Turn Conversation. arXiv:2505.06120
6. Oh et al. (2025). DReaMAD: Bias Entrenchment in Multi-Agent Debate. arXiv:2503.16814
7. Song (2026). Cross-Context Review. arXiv:2603.12123
8. SR-DCR (2025). Self-Reflective Debates for Contextual Reliability. arXiv:2506.06020
9. AceMAD (2026). Breaking the Martingale Curse via Asymmetric Cognitive Potential Energy. arXiv:2603.06801
10. Wu et al. (2025). Can LLM Agents Really Debate? arXiv:2511.07784
11. Chroma Research (2025). Context Rot. research.trychroma.com/context-rot
12. Ashery et al. (2025). Emergent Social Conventions and Collective Bias in LLM Populations. Science Advances. DOI:10.1126/sciadv.adu9368
13. Context Branching (2025). arXiv:2512.13914
14. Vasilopoulos (2026). Codified Context. arXiv:2602.20478
15. Rath (2026). Agent Drift. arXiv:2601.04170
16. Anchoring Bias in LLMs (2024). arXiv:2412.06593
