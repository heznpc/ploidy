# Ploidy: A Framework for Cross-Session Context Asymmetry in Multi-Agent Convergence

## Paper Outline -- Draft v1 (2026-03-15)

---

## 1. Title and Abstract

**Title:** Ploidy: A Framework for Cross-Session Context Asymmetry in Multi-Agent Convergence

**Abstract (Draft):**

Multi-agent debate (MAD) has emerged as a promising paradigm for improving the reasoning fidelity of large language models. However, existing approaches operate within a single session and treat information asymmetry among agents as a deficiency to be corrected through synchronization, shared memory, or context equalization. We argue that this assumption is fundamentally misguided. Drawing on recent theoretical results demonstrating that debate advantage scales linearly with knowledge divergence (Chen et al., 2026), we propose *Ploidy*, a cross-session multi-agent framework that *intentionally constructs* context asymmetry by pairing a context-rich session--one that has accumulated reasoning traces, evidence, and intermediate conclusions--with one or more context-naive sessions that begin from a clean state. The naive sessions achieve an engineered *tabula rasa*--an architectural absence of session-specific context that resists the confirmation bias feedback loops endemic to accumulated-context debate. Unlike Husserl's (1913) phenomenological *epoche*, which requires deliberate effort to suspend judgment, the Fresh session achieves a structural analog through the passive absence of prior context--functionally similar in producing judgment uncontaminated by prior commitment, but passive rather than active. We formalize this as a *ploidy convergence protocol* in which sessions of varying context depth iteratively exchange compressed claims, and convergence is measured not by agreement but by the stability of conclusions under adversarial context asymmetry. Preliminary analysis suggests that Ploidy addresses three open problems simultaneously: belief entrenchment in MAD (Li et al., 2025), premature convergence on majority noise (Wang et al., 2026), and the chat-chamber effect in long-context dialogue. We outline the framework, propose an experimental design spanning factual reasoning, ethical deliberation, and cross-cultural judgment tasks, and identify the theoretical conditions under which intentional asymmetry provably outperforms symmetric debate.

---

## 2. Introduction

### 2.1 Problem Statement

Large language models deployed as multi-agent debate systems face a trilemma:

1. **Belief entrenchment.** Agents that share accumulated context converge prematurely on positions reinforced by the shared evidence base, exhibiting the "chat-chamber effect"--an analogue of epistemic echo chambers in social networks.

2. **Diversity collapse.** Prompt-injection techniques (e.g., assigning "devil's advocate" roles) produce superficial diversity that models learn to discount, yielding cosmetic disagreement without genuine epistemic challenge.

3. **Cross-session coherence.** Real-world agentic deployments span multiple sessions, yet no existing framework addresses how to maintain productive disagreement across session boundaries where context is necessarily discontinuous.

### 2.2 Motivation

The existing literature uniformly frames information asymmetry as pathological. Context synchronization mechanisms (shared memory banks, context compression, retrieval-augmented alignment) aim to bring all agents to the same informational state. But a converging line of theoretical and empirical evidence suggests this is counterproductive:

- Chen et al. (2026) prove that when two debaters possess *identical* knowledge, debate reduces to single-agent reasoning--the adversarial advantage vanishes entirely. The debate premium is a strict function of knowledge divergence.
- Li et al. (2025) demonstrate empirically that MAD suffers from belief entrenchment precisely *because* agents share context and reinforce each other's biases.
- The phenomenological tradition (Husserl, Merleau-Ponty) provides a philosophical framework for *epoche*--the deliberate bracketing of accumulated assumptions--as a method for accessing phenomena without prejudgment. However, epoche is an *active* cognitive achievement; the Fresh session's lack of context is *passive* (architectural absence rather than deliberate suspension). The analogy is structural, not mechanistic.

**Core thesis:** Context asymmetry is not a bug to be patched; it is the *mechanism* by which debate produces epistemic gain. Ploidy operationalizes this insight by making asymmetry a first-class design parameter.

### 2.3 Contributions (Preview)

1. A formal framework (*Ploidy*) for cross-session multi-agent convergence via intentional context asymmetry.
2. A taxonomy of asymmetry regimes (one-sided, compositional, temporal) mapped to the theoretical conditions of Chen et al. (2026).
3. An experimental protocol for measuring convergence quality under controlled asymmetry.
4. Evidence that fresh-session agents naturally resist the chat-chamber effect without requiring adversarial prompt injection.

---

## 3. Related Work

### 3.1 Multi-Agent Debate (MAD) and Its Limitations

**Foundational MAD work.** Du et al. (2023), Liang et al. (2023), and subsequent multi-agent debate systems establish that inter-agent argumentation improves factual accuracy and reasoning depth over single-agent chain-of-thought. However, these operate in a single session with symmetric context.

**Belief entrenchment in MAD.** Li et al. (2025; arXiv 2503.16814) identify a critical failure mode: agents in debate reinforce each other's biases rather than correcting them. Their proposed DReaMAD (Debate with Reasoning and Memory-Augmented Discussion) mitigates this via structured reasoning steps, achieving +9.5% accuracy over ReAct baselines. *Ploidy's positioning:* DReaMAD addresses entrenchment within a session through procedural intervention. Ploidy addresses it structurally--by ensuring one or more agents *cannot* be entrenched because they have no prior context to entrench upon. The approaches are complementary: DReaMAD improves intra-session reasoning; Ploidy improves inter-session diversity.

**Adaptive heterogeneous debate.** A-HMAD (2025, Springer) assigns different specialties to agents, yielding 4--6% accuracy gains and 30% factual error reduction. *Ploidy's positioning:* A-HMAD creates *role* asymmetry (different expertise); Ploidy creates *epistemic state* asymmetry (different information). These are orthogonal axes of heterogeneity. Section 4.5 discusses their combination.

### 3.2 Knowledge Divergence and Debate Theory

**Scaling oversight through divergence.** Chen et al. (2026; arXiv 2603.05293) provide the theoretical foundation Ploidy builds upon. Their central result: the advantage of debate over direct questioning scales linearly with knowledge divergence between debaters, and collapses to zero under identical knowledge. They identify three regimes:
- *Symmetric divergence:* Both agents have unique knowledge. Debate is valuable.
- *One-sided divergence:* One agent knows strictly more. Debate is still valuable (the less-informed agent forces explication).
- *Zero divergence:* Identical knowledge. Debate = single agent.

*Ploidy's positioning:* Ploidy operationalizes the one-sided and compositional divergence regimes by construction. The context-rich session holds accumulated knowledge K_r; the fresh session holds only the base model's parametric knowledge K_0. The divergence K_r \ K_0 is precisely the session-accumulated context, which is also precisely the vector most susceptible to the chat-chamber effect. Debate over this divergent set forces the context-rich session to *justify* its accumulated beliefs to an interlocutor that does not share them.

### 3.3 Context Management in Multi-Agent Systems

**Context learning for discussion.** Wang et al. (2026; arXiv 2602.02350) propose M2CL (Multi-agent Multi-turn Context Learning), which trains context generators to avoid premature convergence on majority noise. *Ploidy's positioning:* M2CL addresses the *quality* of shared context; Ploidy questions whether context should be shared at all. M2CL's trained context generators could serve as the compression mechanism in Ploidy's claim-exchange protocol (Section 4.3).

**Cross-modal memory compression.** (arXiv 2602.00454) addresses the practical constraint that full context sharing is computationally prohibitive. Their compression methods preserve salient information while reducing token count. *Ploidy's positioning:* Ploidy reframes compression as *lossy by design*--the fresh session should receive compressed *claims* rather than compressed *context*, ensuring that the justificatory burden remains on the context-rich session. The compression techniques from this work inform Ploidy's claim extraction module.

### 3.4 Bias and the Chat-Chamber Effect

**Cultural bias in debate.** MACD (arXiv 2601.12091) demonstrates that multi-agent debate can mitigate cultural bias when agents are assigned culturally diverse perspectives. *Ploidy's positioning:* MACD uses prompt-injected cultural roles. Ploidy's fresh session achieves cultural debiasing *without* role assignment, because the model's parametric knowledge (without session-accumulated cultural framing) reverts to a more culturally balanced prior. Section 5.4 proposes a direct comparison.

**Chat-chamber effect.** Analogous to social media echo chambers, accumulated context in long agent sessions creates confirmation bias feedback loops. Each reasoning step that reinforces a conclusion makes subsequent steps more likely to reinforce it further. *Ploidy's positioning:* The fresh session is the structural antidote. It cannot participate in the feedback loop because it has no history to feed back.

### 3.5 Philosophical Foundations

**Engineered tabula rasa.** Husserl's (1913) method of *epoche*--the suspension of the "natural attitude" and all presuppositions about the world--offers a suggestive but imperfect analogy for Ploidy's fresh session. The fresh agent is not ignorant; it possesses the full parametric knowledge of the base model. It merely lacks the *session-specific judgments* that have accumulated. However, the disanalogy is important: epoche is an *active* cognitive achievement requiring deliberate effort, whereas the Fresh session's freedom from prior commitment is *passive*--a consequence of architectural absence of context, not of disciplined suspension. The Fresh session is better characterized as an engineered tabula rasa: structurally uncontaminated by session-specific priors, producing a functional analog of unprejudiced judgment without the active bracketing that Husserl's method demands.

**Gadamerian hermeneutics.** Gadamer (1960) argues that understanding requires a "fusion of horizons" (*Horizontverschmelzung*) between interlocutors with different pre-understandings. Ploidy's convergence protocol can be read as an operationalization of this fusion: sessions with radically different horizons (accumulated vs. fresh) iteratively negotiate toward shared understanding.

---

## 4. Methodology: The Ploidy Framework

### 4.1 Architecture Overview

Ploidy consists of N coupled but informationally asymmetric sessions:

- **Session_R (Rich):** A long-running session that has accumulated context C = {c_1, c_2, ..., c_n} through prior reasoning, evidence gathering, and intermediate conclusions. This session holds the "institutional memory" of the reasoning process.

- **Session_F (Fresh):** A newly instantiated session with no prior context beyond the base model's parametric knowledge theta. This session achieves an engineered tabula rasa by construction--free of session-specific priors through architectural absence of context.

- **Session_I (Intermediate):** Optional additional sessions with partial context, enabling a spectrum of context depths (the "polyploid" configuration).

The sessions communicate through a **Claim Exchange Protocol** (Section 4.3), never through raw context transfer.

### 4.2 Asymmetry as Design Parameter

Define the *asymmetry coefficient* alpha as:

    alpha = |C_R \ C_F| / |C_R U C_F|

where C_R is the effective knowledge of Session_R (parametric + accumulated context) and C_F is the effective knowledge of Session_F (parametric only).

- alpha = 0: Symmetric (all sessions identical). Reduces to standard MAD. Per Chen et al. (2026), no debate advantage.
- alpha = 1: Maximal asymmetry (no shared knowledge). Communication breaks down.
- 0 < alpha < 1: The productive regime. Ploidy targets the *high-alpha* band where divergence is large but a shared parametric base ensures mutual intelligibility.

Key insight: alpha is not a free parameter to be optimized--it is *determined* by the accumulated context length and the degree of reasoning the rich session has performed. Ploidy introduces a **Session Freshness Schedule** that controls when to spawn a fresh session, effectively managing alpha over time.

### 4.3 Claim Exchange Protocol

Communication between sessions proceeds via structured *claims* rather than raw context. Each claim is a triple:

    claim = (proposition, confidence, evidence_summary)

**From Session_R to Session_F:**
1. Session_R extracts its top-k current beliefs as claims.
2. Each claim is compressed to remove session-specific reasoning traces (retaining only the proposition, a calibrated confidence score, and a one-sentence evidence summary).
3. Claims are presented to Session_F as *assertions to be evaluated*, not as conclusions to be accepted.

**From Session_F to Session_R:**
1. Session_F evaluates each claim using only its parametric knowledge and first-principles reasoning.
2. For each claim, Session_F returns a *verdict*: {accept, challenge, reframe, underdetermined}.
3. Challenges must include a *counter-argument* or *alternative framing*.
4. Session_R must respond to challenges substantively--it cannot simply reassert.

### 4.4 Convergence Criteria

Ploidy does *not* define convergence as agreement. Instead, convergence is measured by **stability under re-examination**:

- **Claim stability:** A claim is *stable* if it survives challenge from m independent fresh sessions (m >= 3).
- **Reasoning stability:** The justification graph for a claim is stable if the fresh session's challenges do not introduce novel, unaddressed counter-arguments after k rounds.
- **Confidence calibration:** Post-debate confidence scores should be better calibrated than pre-debate scores (measured against ground truth where available).

A *ploidy convergence score* P is defined as the harmonic mean of claim stability and confidence calibration.

### 4.5 Extension: Ploidy x A-HMAD

Ploidy's epistemic asymmetry is orthogonal to A-HMAD's role asymmetry. The combined system uses:
- Multiple Session_R instances with different *specialties* (per A-HMAD).
- A single Session_F with no specialty assignment, acting as a generalist challenger.
- The generalist fresh session is particularly effective at identifying *inter-specialty blind spots*--assumptions shared by all specialists but not warranted by general knowledge.

### 4.6 Session Freshness Schedule

Not every reasoning step requires a fresh session. Ploidy introduces a heuristic schedule:

- **Trigger conditions for spawning Session_F:**
  - Accumulated context exceeds length threshold L_max.
  - Internal confidence exceeds threshold p_max (overconfidence signal).
  - Reasoning graph shows convergence (declining entropy of claim distribution).
  - Explicit user or orchestrator request.

- **Recycling Session_F:** After each exchange round, Session_F is discarded. A new Session_F is instantiated for subsequent rounds. This prevents Session_F from itself accumulating context and losing its tabula rasa property.

---

## 5. Experimental Design

### 5.1 Research Questions

- **RQ1:** Does Ploidy's intentional asymmetry improve factual accuracy over symmetric MAD on knowledge-intensive tasks?
- **RQ2:** Does the fresh session resist the chat-chamber effect more effectively than prompt-injected adversarial roles?
- **RQ3:** How does the asymmetry coefficient alpha correlate with debate quality, and is there an optimal band?
- **RQ4:** Does Ploidy reduce cultural and cognitive bias compared to single-session debate?
- **RQ5:** What is the computational cost-accuracy tradeoff relative to baselines?

### 5.2 Tasks and Datasets

| Task Category | Dataset | Rationale |
|---------------|---------|-----------|
| Factual reasoning | MMLU-Pro, GPQA | Standard knowledge-intensive QA; enables comparison with DReaMAD |
| Long-horizon reasoning | GSM-Hard, MATH-500 | Multi-step reasoning where error accumulation is measurable |
| Ethical deliberation | Scruples, ETHICS benchmark | No single ground truth; tests convergence quality vs. agreement pressure |
| Cross-cultural judgment | CulturalBench, MACD evaluation set | Direct comparison with MACD's prompt-based cultural diversity |
| Open-ended analysis | FreshQA (time-sensitive), StrategyQA | Tests whether accumulated context helps or hurts on ambiguous queries |
| Adversarial robustness | TruthfulQA, HaluEval | Tests whether fresh sessions catch hallucinations the rich session has committed to |

### 5.3 Baselines

1. **Single agent (no debate):** Standard chain-of-thought prompting.
2. **Symmetric MAD:** Standard multi-agent debate with shared context (Du et al., 2023).
3. **DReaMAD:** Li et al.'s (2025) reasoning-augmented debate.
4. **A-HMAD:** Heterogeneous specialist debate.
5. **M2CL:** Context-learned discussion (Wang et al., 2026).
6. **Prompt-injected adversary:** One agent assigned a "devil's advocate" role within a single session.
7. **Random context ablation:** One agent receives a random subset of context (tests whether *any* asymmetry helps, or only the specific fresh-vs-rich structure).

### 5.4 Metrics

- **Accuracy** (factual tasks): Exact match and F1 against ground truth.
- **Calibration** (all tasks): Expected Calibration Error (ECE) of post-debate confidence scores.
- **Diversity** (all tasks): Semantic diversity of arguments generated during debate (measured via embedding cosine distance).
- **Entrenchment index** (all tasks): Proportion of initial claims that survive debate unchanged (lower = less entrenchment, *up to a point*).
- **Convergence efficiency** (all tasks): Number of exchange rounds to reach stability threshold.
- **Cultural bias score** (cultural tasks): Variance of responses across culturally framed queries (per MACD's protocol).
- **Token cost** (all tasks): Total tokens consumed, as a practical measure of computational overhead.

### 5.5 Ablation Studies

1. **Freshness ablation:** Vary the amount of context shared with Session_F (from zero to full context) to trace the accuracy-vs-asymmetry curve.
2. **Compression ablation:** Compare claim-only exchange vs. compressed-context exchange vs. full-context exchange.
3. **Schedule ablation:** Compare fixed-interval fresh session spawning vs. the heuristic trigger conditions in Section 4.6.
4. **Recycling ablation:** Compare discarding Session_F after each round vs. allowing it to accumulate cross-round context.
5. **Model pairing ablation:** Test Ploidy with heterogeneous model pairs (e.g., Session_R = GPT-5, Session_F = Claude Opus) to explore whether model diversity compounds with context diversity.
6. **Ploidy level ablation:** Compare haploid (1 session), diploid (2 sessions), triploid (3 sessions), and higher ploidy configurations to measure the marginal value of additional sessions.

### 5.6 Hypotheses

- **H1:** Ploidy outperforms symmetric MAD on factual accuracy by a margin proportional to the accumulated context length (per the linear scaling result of Chen et al., 2026).
- **H2:** Ploidy's fresh session produces higher argument diversity than prompt-injected adversarial roles, as measured by embedding distance.
- **H3:** The optimal alpha band lies between 0.4 and 0.8; below 0.4, divergence is insufficient; above 0.8, mutual intelligibility breaks down.
- **H4:** Ploidy reduces entrenchment index by at least 20% relative to standard MAD on tasks exceeding 10 reasoning steps.
- **H5:** The recycling ablation (discarding Session_F each round) outperforms the persistent ablation, confirming that freshness must be maintained.
- **H6:** Diminishing returns set in beyond triploid (3 sessions) for most tasks, with the optimal ploidy level being task-dependent.

---

## 6. Expected Contributions

### 6.1 Theoretical Contributions

1. **Reframing asymmetry.** The first work to argue that information asymmetry in multi-agent LLM systems is a *design feature* rather than a failure mode. This challenges a foundational assumption in the multi-agent debate literature.

2. **Cross-session formalization.** A formal model for multi-agent debate that spans session boundaries, introducing the asymmetry coefficient alpha and the claim exchange protocol as first-class constructs.

3. **Connecting debate theory to phenomenology.** A novel bridge between Chen et al.'s (2026) mathematical framework for knowledge divergence and the phenomenological tradition of epoche, providing philosophical grounding for a computational technique.

### 6.2 Practical Contributions

4. **Ploidy framework.** An implementable architecture for cross-session multi-agent convergence that requires no fine-tuning, no specialized training, and no modifications to the base model. It operates purely at the orchestration layer.

5. **Chat-chamber mitigation.** A structural solution to the chat-chamber effect that does not rely on prompt engineering or adversarial role assignment--both of which are brittle and model-dependent.

6. **Session freshness schedule.** Practical heuristics for determining when accumulated context has become counterproductive and a fresh perspective is needed.

### 6.3 Implications for AI Safety and Alignment

7. **Scalable oversight.** Ploidy extends the scalable oversight agenda (Irving et al., 2018; Chen et al., 2026) by demonstrating a practical mechanism for maintaining the debate advantage in deployed systems where context accumulates over time.

8. **Debiasing without explicit bias modeling.** By leveraging the base model's parametric prior as a debiasing baseline, Ploidy avoids the need to explicitly model and enumerate biases--an approach that is inherently incomplete.

---

## 7. Target Venues

### 7.1 Primary Targets (Top-tier AI / NLP)

| Venue | Fit Rationale | Deadline (approx.) |
|-------|---------------|---------------------|
| **NeurIPS 2026** | Strong fit for the theoretical framing (asymmetry coefficient, convergence formalization) and the experimental breadth. NeurIPS values novel frameworks with rigorous evaluation. | May 2026 |
| **ICLR 2027** | Excellent fit if experimental results emphasize the learning/representation angle (what does the fresh session "know" differently?). | Sep 2026 |
| **ACL 2027** | Strong fit for the NLP-specific evaluation (factual QA, cultural bias, calibration). The philosophical framing (epoche) may appeal to ACL's growing interest in interdisciplinary work. | Jan 2027 |

### 7.2 Secondary Targets

| Venue | Fit Rationale |
|-------|---------------|
| **AAAI 2027** | Broad AI audience; the AI safety implications (Section 6.3) align with AAAI's scope. |
| **AAMAS 2027** | Multi-agent systems venue; the cross-session protocol is a natural fit. |
| **COLM 2027** | Newer venue focused on language models; strong topical alignment. |

### 7.3 Workshop Targets (for early feedback)

| Workshop | Fit |
|----------|-----|
| NeurIPS 2026 Workshop on Foundation Model Agents | Cross-session agent architecture |
| ICML 2026 Workshop on LLM Cognition | Epoche framing, phenomenological connection |
| ACL 2026 Workshop on Trustworthy NLP | Debiasing, chat-chamber mitigation |

### 7.4 Journal Option

| Journal | Rationale |
|---------|-----------|
| **JMLR** | If the theoretical contributions (asymmetry coefficient, convergence proofs) are substantial enough to warrant a longer format. |
| **TACL** | If the NLP-specific experiments are the strongest contribution. |

---

## 8. Open Questions and Risks

1. **Operationalizing alpha.** The asymmetry coefficient is defined over knowledge sets C_R and C_F, but measuring these sets in practice requires approximation. Possible proxies: context token count, number of reasoning steps, entropy of the claim distribution.

2. **Freshness as naivete.** A genuinely fresh session may lack task-specific understanding that is *legitimate* (not biased). The claim exchange protocol must distinguish between session-accumulated bias and session-accumulated knowledge. This is the central design tension.

3. **Computational cost.** Spawning a new session for each challenge round is expensive. The session freshness schedule (Section 4.6) must balance debiasing benefit against token cost. Cost-per-accuracy-point analysis is essential.

4. **Reproducibility.** Cross-session experiments depend on the model's behavior across independent API calls. Temperature, system prompt variations, and model updates may introduce confounds. The experimental protocol must control for these.

5. **Generality.** The ploidy framework naturally supports N-session (polyploid) interaction--e.g., sessions of varying freshness. Determining the optimal ploidy level for different task categories is an open empirical question.

---

## 9. Suggested Paper Structure and Page Budget

(Targeting 8-page NeurIPS format + appendix)

| Section | Pages | Content |
|---------|-------|---------|
| Abstract | 0.3 | As drafted above |
| Introduction | 1.2 | Problem, motivation, contributions |
| Related Work | 1.5 | Positioned against all 7 reference papers |
| The Ploidy Framework | 2.0 | Architecture, asymmetry coefficient, claim exchange, convergence criteria |
| Experiments | 2.0 | Setup, results, ablations |
| Discussion | 0.7 | Limitations, broader impact, future work |
| Conclusion | 0.3 | Summary of contributions |
| *Appendix* | 4--6 | Proofs, full ablation tables, qualitative examples, prompt templates |

---

## 10. Key Terminology

| Term | Definition |
|------|------------|
| **Ploidy** | A cross-session debate framework supporting N sessions with varying context depths (from rich to fresh) |
| **Session_R** | The context-rich (accumulated) session |
| **Session_F** | The context-fresh (tabula rasa) session |
| **Session_I** | Optional intermediate sessions with partial context |
| **Engineered tabula rasa** | Architectural absence of session-specific context; the Fresh session's passive analog to phenomenological epoche, achieving unprejudiced judgment through context absence rather than active suspension |
| **Asymmetry coefficient (alpha)** | Normalized measure of knowledge divergence between sessions |
| **Claim exchange protocol** | Structured communication via (proposition, confidence, evidence_summary) triples |
| **Chat-chamber effect** | Confirmation bias feedback loop in accumulated-context dialogue |
| **Ploidy convergence score (P)** | Harmonic mean of claim stability and confidence calibration |
| **Session freshness schedule** | Heuristic triggers for spawning a new Session_F |
| **Haploid** | Single-session configuration (1n) -- baseline, no debate |
| **Diploid** | Two-session configuration (2n) -- one rich, one fresh |
| **Triploid** | Three-session configuration (3n) -- one rich, two fresh (or varying depths) |
| **Polyploid** | N-session configuration (Nn) -- multiple sessions of varying freshness |

---

*Outline drafted 2026-03-15. Pre-submission target: NeurIPS 2026.*
