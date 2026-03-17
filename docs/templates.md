# Debate Templates

Copy-paste templates for common debate scenarios. Use these as prompts when starting a Ploidy debate.

## Architecture Decision

**Deep session prompt:**
> Start a Ploidy debate: "[QUESTION]"
>
> Context: We have [TEAM SIZE] engineers, [SERVICE COUNT] services, and [KEY CONSTRAINT]. Our current approach is [CURRENT STATE]. Consider our deployment pipeline, team structure, and operational burden.

**Fresh session prompt:**
> Join Ploidy debate [DEBATE_ID]
>
> Analyze the architecture question purely on technical merit. You have no context about the existing system — evaluate based on first principles.

### Examples

| Question | Why it works for Ploidy |
|----------|------------------------|
| Monorepo vs polyrepo? | Deep knows team dependencies; Fresh sees coupling risks |
| REST vs gRPC for internal APIs? | Deep knows existing middleware; Fresh evaluates protocol merits |
| SQL vs NoSQL for this data model? | Deep knows query patterns; Fresh spots schema assumptions |
| Microservices vs modular monolith? | Deep knows operational burden; Fresh questions necessity |

---

## Code Review

**Deep session prompt:**
> Start a Ploidy debate: "Review this implementation approach for [FEATURE]"
>
> Context: [Paste the relevant code or describe the approach]. This builds on our existing [MODULE] which handles [RESPONSIBILITY]. We chose this approach because [REASON].

**Fresh session prompt:**
> Join Ploidy debate [DEBATE_ID]
>
> Review the implementation for correctness, edge cases, and design issues. No prior knowledge of the codebase is needed.

---

## Technology Selection

**Deep session prompt:**
> Start a Ploidy debate: "Should we adopt [TECHNOLOGY] for [USE CASE]?"
>
> Context: We currently use [CURRENT TECH]. Our team has experience with [SKILLS]. Key constraints: [CONSTRAINTS]. Timeline: [DEADLINE].

**Fresh session prompt:**
> Join Ploidy debate [DEBATE_ID]
>
> Evaluate the technology choice on its own merits. Consider maturity, community, performance, and long-term maintenance.

---

## Refactoring Decision

**Deep session prompt:**
> Start a Ploidy debate: "Should we refactor [MODULE] now or ship the feature first?"
>
> Context: [MODULE] has [TECH DEBT DESCRIPTION]. The upcoming feature requires [CHANGES]. Refactoring would take approximately [TIME]. The feature deadline is [DATE].

**Fresh session prompt:**
> Join Ploidy debate [DEBATE_ID]
>
> Given only the refactoring question, evaluate the trade-off between technical debt and delivery speed.

---

## Security Audit

**Deep session prompt:**
> Start a Ploidy debate: "Is our authentication flow for [FEATURE] secure?"
>
> Context: [Describe the auth flow]. We use [AUTH PROVIDER] with [TOKEN TYPE]. The flow handles [SENSITIVE DATA]. Previous security review noted [PAST ISSUES].

**Fresh session prompt:**
> Join Ploidy debate [DEBATE_ID]
>
> Audit the authentication flow for vulnerabilities. Apply OWASP Top 10 and assume zero trust.

---

## Tips

1. **Be specific in the Deep prompt** — include real constraints, team size, deadlines
2. **Keep the Fresh prompt minimal** — the whole point is zero context
3. **Architecture decisions work best** — they have clear trade-offs that benefit from dual perspectives
4. **Watch for `propose_alternative`** — Fresh sessions often find third options that Deep sessions are blind to
5. **Irreducible disagreements are valuable** — they flag decisions that need human judgment, not more AI debate
