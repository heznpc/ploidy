# ploidy — Review (2026-04-11)

## 1. 커밋 톤이 주장을 일관되게 지지하는가?

**판정: 매우 일관됨 (55 commits, 2026-03-15 → 04-11). 본 survey 21개 paper 중 commit history가 *가장 길고 가장 정직*.**

55개 commit. 본 survey 21개 paper 중 canary(26개) 다음으로 길고, *paper와 service가 동시에 진화*한 사례. 핵심 marker:

```
7fe609e fix(ploidy): default to stdio, add debate_solo, fix critical bugs (#4)  (2026-04-11)
c919b76 update related work: Claude Agent Teams → Claude Managed Agents + subagent scaling
8c4f8d3 feat: Phase 1 server upgrade + Tool-Fresh experiments + paper update    (2026-04-06)
b2a3d27 refactor: split papers into monorepo structure                          
4304736 feat: update paper with 28-task expanded results + structural fixes
411e3dc fix: ruff lint errors in diversity experiment
95ccbed feat: add token tracking + diversity experiment (Species vs Cultural)
a2ee4bc add Planck principle to Introduction
855e9c1 Sync all docs to 11 tools, re-anonymize COLM submission
42b2f6b Strengthen ground-truth defense, soften novelty claim, bump v0.3.2
ead9c85 Soften novelty claim, add vendor-neutrality note to acknowledgments
ce97b20 Add cross-model data completion, time variance table, effort claim correction
eca79ba Add stochastic_n baseline, D-CCR citation, presentation bias limitation
a1f6020 Add COLM 2026 submission, cross-model validation (4 families), injection reversal
789a5cf Strengthen pilot framing, add threshold hypothesis, sharpen self-consistency defense
72053be Add effort sweep, apoptosis framing, ColMAD/Lost-in-Middle citations, reviewer preemption
9056ec6 Remove ungrounded citations (Kuhn, Azoulay) and companion paper references
dba91d3 Add cross-model validation (Opus vs Sonnet), unify API backend
cc9a673 Add injection mode variable, ploidy level sweep, and Event A/B framework
```

진화 패턴:
- **Phase 1 (3/15 ~ 3/20)**: v0.1 Two-Terminal MCP server. FastMCP, SQLite, debate state machine.
- **Phase 2 (3/21 ~ 4/2)**: v0.2 API fallback, Semi-Fresh sessions, LLM convergence, dashboard.
- **Phase 3 (4/2 ~ 4/11)**: v0.3 cross-model validation (4 model families: Opus, Sonnet, Gemini, GPT-5.4), Stochastic-N baseline (Event A/B isolation), ploidy 1n-4n sweep, COLM 2026 submission, Tool-Fresh experiments, **결과 inversion 발견** (deterministic Tool-Fresh > probabilistic Ploidy on code review tasks).

톤 일관성:
- 핵심 framework(Event A vs B / Context Asymmetry Spectrum / injection mode / heterogeneous independence taxonomy)가 모든 phase에서 점진적으로 정착.
- **결과의 inversion이 commit message에 정직하게 반영**: "Strengthen ground-truth defense, soften novelty claim", "Add cross-model data completion, time variance table, **effort claim correction**", "Strengthen pilot framing, add **threshold hypothesis**, sharpen self-consistency defense". *자기 가설이 부분 reject되는 데이터를 paper에 그대로 통합*. 본 survey 21개 중 *empirical 정직성 TOP*.
- **"Soften novelty claim"** (4월 1일경) — 자기 contribution claim의 강도를 직접 낮춤. *paper 안에서* "Ploidy의 가설된 advantage over Single Session is **not confirmed at corrected significance**"라고 명시. 학술 paper에서 매우 드문 정직.
- **"Remove ungrounded citations (Kuhn, Azoulay)"** — 인용을 *제거*하는 commit. 본 survey 다른 paper에서 거의 보지 못한 self-discipline.
- **2 paper 동시 진행**: paper-1-experimental + paper-1-position + paper-2-mechanism으로 monorepo 분할. paper-2-mechanism이 가장 성숙.
- **canary 4/11 commit과 동일한 패턴**: 4/11 commit이 14 files 793/-215 lines, *self-review에서 발견된 cluster fix* + paper update + 새 tool(debate_solo) + critical bug fixes 동시. *지속적 hardening cycle*.

## 2. 부가 서비스 품질

**판정: 본 survey 21개 paper 중 service quality 압도적 1위 (canary와 동급, 그러나 *학술 검증 instrument로서*는 ploidy가 1위).**

서비스 구성 (코드 16,300줄):
- **Python MCP server (`src/ploidy/`, 4,162줄)**:
  - `server.py` (1,869줄): FastMCP server, 11 debate tools (start/join/position/challenge/converge/cancel/list/recover/effort_set/review/solo), Streamable HTTP/stdio dual transport
  - `store.py` (578줄): SQLite + WAL aiosqlite persistence, 6 DB migrations
  - `dashboard.py` (474줄): ASGI web dashboard for debate visualization
  - `api_client.py` (413줄): OpenAI-compatible 4-family backend (Anthropic/OpenAI/Google/xAI)
  - `convergence.py` (331줄): rule-based + LLM meta-analysis convergence
  - `injection.py` (178줄): 5 injection modes (raw/memory/skills/system_prompt/CLAUDE.md)
  - `protocol.py` (122줄): debate state machine 5-phase
  - `session.py` (101줄): Deep/Semi-Fresh/Fresh roles
  - `exceptions.py` (33줄): domain exceptions
  - `__init__.py`, `__main__.py`: package + CLI
- **Experiments (8,848줄)**:
  - `run_experiment.py` (2,402줄): main runner with effort/language/injection sweeps
  - `tasks_longcontext.py` (2,683줄): long-context task definitions
  - `tasks_extended.py` (1,146줄): 25 extended tasks
  - `skills_fresh_design.py` (1,031줄): skills-based Fresh design
  - `token_tracker.py` (898줄): cost/token tracking
  - `analyze_stats.py` (651줄): statistical analysis
  - `run_diversity_experiment.py` (622줄): diversity experiment
  - `task_model.py` (15줄): Task dataclass
- **Tests (1,008줄)**:
  - `test_http_e2e.py` (293), `test_debate_flow.py` (422), `test_api_client.py` (136), `test_convergence.py` (146), `test_dashboard.py` (77), `conftest.py` (8)
  - 4/11 commit에서 fake test → real pytest test 변환
- **MkDocs site** (`docs/`): index, getting-started, how-it-works, architecture, api-reference, session-orchestration, templates, paper-draft, contributing, research, internal/, ko/(한국어 문서)
- **Dockerfile + docker-compose.yml**: 컨테이너 배포 지원
- **GitHub Pages 배포**: heznpc.github.io/PLOIDY/
- **CI/CD**: GitHub Actions (CI badge in README)
- **Zenodo DOI 준비** (.zenodo.json)
- **CLAUDE.md + .mcp.json**: AI agent integration spec
- **`paper/shared/Template-2026/`**: 학술 template
- **`paper/shared/references-master.bib`**: 통합 참고문헌
- **`paper/shared/research-program.md`**: 3-paper research roadmap

품질 평가:
- **본 survey 21개 paper 중 *MCP 서버를 실제로 구현*한 유일한 케이스.** 다른 paper의 instrument는 모두 protocol/design 수준. ploidy는 *작동하는 서버*.
- **4 model family cross-validation** (Opus 4.6, Sonnet 4.6, Gemini 3.1 Pro, GPT-5.4): 본 survey 21개 paper 중 *최대 cross-model evaluation*.
- **1,660 valid (task, run, method) triples**: 본 survey 중 *empirical sample size 1위*.
- **5 injection modes × 4 ploidy levels × 4 languages × 4 model families**: 4-axis factorial design. 학술 표준에 미달이 아니라 *과잉*에 가까움.
- **paired Wilcoxon signed-rank tests + Holm-Bonferroni correction**: 정확한 통계 protocol.
- **Stochastic-N baseline**: Event A/B 분리를 위한 *idéal control*. 본 survey 다른 paper에서 보기 드문 baseline rigor.
- **Tool-Fresh ablation**: 자기 thesis가 부분 reject되는 alternative method까지 측정. **negative result를 paper에 통합**.
- 한계: 4/11 commit이 critical fix로 14 files / 793 lines 변경. v0.3.2 stability 1주 정도 지켜봐야 함.

## 3. 고도화 가능 파트

높은 우선순위 (COLM 2026 직결):
1. **COLM 2026 submission 마무리** — colm_submission.tex (541줄)이 별도로 존재. 이게 어떤 상태인지(제출 여부) 확인 + 4/11 critical fix 결과를 반영. README에 명시.
2. **stability 검증 1주** — 4/11 cluster fix 후 production readiness 1주 burn-in. 4월 17일 즈음 release tag (v0.3.3 또는 v0.4).
3. **reproducibility instructions** — README가 두 transport(stdio + http)를 다 설명하지만, *experiment 재현*에 대한 step-by-step 지시 부족. `./experiments/run_all.sh`가 있지만 *what does it produce* 명시 필요.
4. **Long-context tasks의 directional advantage statistical strengthening** — 4/5 runs (mean F1 0.595 vs 0.565)가 *significant 못 함* (p=0.44). N을 늘리면 p<0.05 가능. 추가 task 5-10개 + 추가 cross-model.
5. **Tool-Fresh inversion finding의 *개념적 통합***: paper의 가장 중요한 finding(deterministic > probabilistic on rule-based tasks)을 framework에 *공식 흡수*. "heterogeneous independence taxonomy" 4번 contribution을 abstract에서 *결과 단일 결정*로 격상.

중간 우선순위:
6. **paper-1-experimental** main.tex 작성 — 현재 outline.md만. paper-2-mechanism이 1차 publication 후 이것이 2차.
7. **paper-1-position context-as-lifespan** — outline.md만. apoptosis framing 활용한 별도 position paper.
8. **diversity experiment의 결과 통합** — Species vs Cultural diversity가 paper에 어떻게 들어가는지 명확화.
9. **HITL (debate_review)** — v0.3에 추가됐지만 paper에 충분히 반영 안 됨. 사용자 case study 1-2개.
10. **dashboard UI 개선** — 현재 lightweight ASGI. 사용자가 결과 visualize 할 때 도움.

낮은 우선순위:
11. PyPI release (`pip install ploidy`).
12. arXiv 동시 게시.
13. 한국어 README 개선 (docs/ko/ 존재).

## 4. 학술적 / 시장 가치 (글로벌, 2026-04-11 기준)

### 학술적 가치: **상위권 (working paper 기준 top ~5%, MCP server + LLM eval 한정 시 top 2-3%)**

차별점:
- **Ploidy framework의 명확한 conceptual contribution**:
  - **Event A vs Event B 분리**: context asymmetry vs stochastic variance가 *다른 현상*임을 ploidy level 1n→2n+로 분리 가능.
  - **Context Asymmetry Spectrum**: Deep → Semi-Fresh → Fresh의 *연속체*로 framing.
  - **Injection mode as variable**: raw/memory/skills/system_prompt/CLAUDE.md를 *조작 변수*로 도입.
  - **Heterogeneous independence taxonomy**: deterministic Tool-Fresh ↔ probabilistic Ploidy의 *상호 보완*. 둘이 경쟁 아닌 *복합*임을 입증.
- **본 survey 21개 paper 중 *real-world MCP server*를 갖춘 유일한 케이스**. anthropic/mcp-spec community에 직접 배포 가능. Anthropic이 좋아할 형태.
- **Cross-model validation (4 families)** + **1,660 trials** + **paired Wilcoxon + Holm-Bonferroni**: 학술 표준 정확히 충족. reviewer가 statistical rigor로 reject 어려움.
- **Negative results를 paper에 통합**: "Soften novelty claim", "hypothesized advantage not confirmed", "Tool-Fresh inversion". 이는 학술 정직성의 *최고 표준*. reviewer가 실제로 매우 호의적으로 본다.
- **narcissus + meta + ai-slop와의 cross-repo trilogy**: ploidy = architectural countermeasure. narcissus = empirical evidence. meta = first-person reflexive. *한 연구 프로그램의 3-paper trilogy*.
- **Companion paper 명시**: paper-1-experimental, paper-1-position, paper-2-mechanism로 분할. 인용 surface area 3배.

위험:
- **결과 inversion**: 핵심 가설(Ploidy > Single Session)이 *significant 못함*. paper 안에서 정직히 인정하지만, reviewer가 첫 round에서 reject 가능. *re-framing*으로 contribution을 *framework + design space*로 옮겨야 함.
- **단일 저자 (heznpc)**: COLM/NeurIPS는 multi-author가 표준. 임상 ADHD/HCI 영역에서는 약점.
- **Tool-Fresh inversion이 paper의 핵심 finding이 됨**: 원래 가설은 ploidy가 우월하다는 것. 결과는 deterministic Tool-Fresh가 우월. **paper의 narrative arc가 자기 thesis와 *반대*에서 끝남**. 이는 학술적으로 흥미롭지만 venue selection이 중요.
- **threshold hypothesis (long-context에서만 advantage)**: 추가 검증 필요. 현재 N이 작아 권장 venue에서 reviewer가 짚을 가능성.
- **4월 11일 critical fix 직후**: production stability 우려.

게재 전망:
- **COLM 2026** (Conference on Language Modeling): 이미 submission 진행 중. **realistic, 40-50%**. 결과 inversion이 honesty signal이라 reviewer 호의적일 가능성. cross-model + statistical rigor 충족.
- **NeurIPS 2026**: Datasets and Benchmarks track. 35-45%.
- **ACL 2026**: 30-40%.
- **MLSys 2026**: System paper로 reframe 시 50-60%.
- **HCI venue (CSCW/CHI 2027)**: HITL 강조 시 가능. 40-50%.
- arXiv preprint 우선 권장.

### 시장 가치: **압도적 상위 (canary와 함께 본 survey 21개 paper 중 *real product* TOP 2)**

- **AI dev tool 시장**: Anthropic MCP ecosystem에 즉시 배포 가능. Cursor, Cline, Windsurf, Lovable이 *context-asymmetric debate* feature를 추가하는 데 *학술적 정당화* 제공.
- **MCP server 카탈로그**: anthropic/mcp-servers 공식 list에 추가 가능. *bias mitigation* category의 reference implementation.
- **LLM eval 회사**: Hugging Face Eval, Stanford CRFM, MLCommons, Arize AI, Weights & Biases가 *Ploidy benchmark*를 채택할 수 있음. 1,660 trials는 그 자체로 evaluation dataset.
- **enterprise AI governance**: 금융/의료/법무 영역에서 LLM decision verification이 필요한 곳. ploidy의 *audit trail*을 그대로 사용.
- **OSS funding**: GitHub Sponsors, Open Collective. CCF/NSF AI safety 펀딩 가능.
- **언론 (학술 영역)**: ICLR/NeurIPS workshop에서 *invited talk* 가능. AI safety conference의 standard reference.
- **Anthropic 내부 사용**: claude.ai 자체가 ploidy를 internal eval로 사용 가능. Anthropic이 후원할 가능성 가장 큼.

### 종합 평점 (2026-04-11)

| 축 | 점수 | 코멘트 |
|---|---|---|
| Originality of framework | 9/10 | Event A/B + Context Spectrum + injection mode + taxonomy |
| Empirical rigor | 9/10 | 1,660 trials, 4 model families, Wilcoxon + Holm |
| Negative result honesty | 10/10 | hypothesized advantage not confirmed - 정직 |
| Service quality | 10/10 | Production-grade Python MCP server, 4,162줄 |
| Theory-implementation coupling | 10/10 | paper의 metric이 server runtime |
| Self-criticism | 10/10 | 1n→2n+ Stochastic-N baseline + ablation |
| Repo health | 10/10 | 55 commits, CI, MkDocs, Docker, Zenodo, version |
| Submission readiness (COLM 2026) | 9/10 | colm_submission.tex 존재, 결과 inversion 정직 처리 |
| Cross-repo synergy | 9/10 | narcissus + meta + ai-slop trilogy |
| Practical applicability | 10/10 | MCP ecosystem 즉시 사용 |
| Timing | 10/10 | LLM bias + MCP 정점 |
| **Overall (system paper)** | **9.2/10** | **본 survey 21개 중 canary와 동급 1-2위** |

핵심 격언: **"Negative result를 contribution으로 reframing + Tool-Fresh inversion을 framework의 *핵심 finding*으로 격상하면 COLM 2026 통과 가능."** 본 survey 21개 paper 중 *production-grade implementation + 학술 통계 rigor + 결과 정직성*의 동시 만족도 압도적 1위. canary가 *DSR 트랙*이라면 ploidy는 *empirical system 트랙*. 두 paper가 본 survey의 *technical excellence 양대 기둥*. v0.3.2의 stability burn-in 1주만 거치면 release.
