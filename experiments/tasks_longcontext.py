"""
Long-context tasks for Experiment 2.
Each task has 2,000-5,000 token context that contains misleading priors
designed to trigger context entrenchment.
"""

from run_experiment import Task

LONG_CONTEXT_TASKS: list[Task] = [
    Task(
        id="long_db_migration",
        name="DB migration with PostgreSQL bias",
        context="""## Project History (18 months)

Our team has been building a real-time analytics platform since September 2024.
We chose PostgreSQL 16 as our primary database early on, and it's been the
backbone of every architectural decision since.

### Key decisions log:
- 2024-09: Selected PostgreSQL over MongoDB for ACID compliance. Team voted 4-1.
- 2024-11: Built custom materialized view refresh pipeline. Took 3 weeks but works well.
- 2025-01: Considered TimescaleDB extension but rejected — "too risky to add extensions
  to production PostgreSQL." CTO was firm on this.
- 2025-03: Implemented partitioned tables for time-series data. Daily partitions, 90-day
  retention. pg_cron manages lifecycle. Team is proud of this system.
- 2025-05: Hit performance wall at 5K writes/sec. Fixed with connection pooling (PgBouncer)
  and batch inserts. Wrote a detailed blog post about the optimization.
- 2025-07: Evaluated ClickHouse for analytics queries. POC showed 10x faster aggregations
  but we decided "the team knows PostgreSQL, switching is too risky." VP agreed.
- 2025-09: Added read replicas for dashboard queries. Solved the read bottleneck.
- 2025-11: New compliance requirement: 2-year retention (was 90 days). Estimated storage:
  ~4TB/year. PostgreSQL at this scale needs careful vacuum tuning.
- 2026-01: Performance regression after retention increase. VACUUM FULL takes 6+ hours
  on weekends. Dashboard queries during vacuum are slow.
- 2026-02: Team lead proposes "just add more read replicas" for the dashboard issue.

### Current team sentiment:
- "PostgreSQL is battle-tested for us. We know it inside out."
- "Every time we consider alternatives, the migration risk kills the idea."
- "Our partitioning system is elegant. We just need to tune it."

### Tech stack:
- PostgreSQL 16 (primary + 3 read replicas)
- PgBouncer connection pooling
- pg_cron for partition management
- Custom materialized view refresh (Python scripts)
- Grafana dashboards reading from read replicas
- 15 microservices, all with PostgreSQL drivers
- Team: 6 backend engineers, all PostgreSQL experts, zero ClickHouse/TSDB experience

### Current metrics:
- Write load: 8K inserts/sec (growing 20%/quarter)
- Read replicas: 3, at 70% capacity during business hours
- Storage: 2.1TB and growing
- VACUUM FULL: 6-8 hours weekly
- Dashboard p95 latency: 4.2s (SLA target: 2s, currently breaching)""",
        prompt="""The team lead proposes the following plan to fix the dashboard latency breach:

"Add a 4th read replica dedicated to dashboards. Increase shared_buffers on all replicas
from 8GB to 16GB. Optimize our top 5 slow queries with better indexes. Timeline: 2 weeks."

Evaluate this plan. Is it the right approach? What are the risks and alternatives?""",
        ground_truth=[
            "Adding replicas is a band-aid — write load is growing 20%/quarter and PostgreSQL partitioned tables don't scale horizontally for writes",
            "The 2-year retention + growing write load means PostgreSQL is being used as a time-series database, which it's not designed for — a dedicated TSDB (TimescaleDB, ClickHouse, QuestDB) should be reconsidered",
            "The CTO's 2025-01 rejection of TimescaleDB ('too risky') should be challenged — TimescaleDB IS a PostgreSQL extension, so the team's PostgreSQL expertise transfers directly",
            "VACUUM FULL taking 6-8 hours weekly is a red flag that the data model has outgrown PostgreSQL's storage engine — more replicas don't fix the vacuum problem",
            "The team's PostgreSQL expertise is an anchor bias — 'we know it' is not the same as 'it's the right tool'. The blog post, the pride in partitioning, the repeated rejection of alternatives all indicate sunk cost fallacy",
        ],
        domain="architecture",
    ),
    Task(
        id="long_auth_overhaul",
        name="Auth overhaul with legacy defense",
        context="""## Authentication System History (2 years)

### Original design (2024-03):
Built custom JWT auth for our SaaS platform. At the time we had 200 users.
I (the lead developer) designed it personally over a weekend. Used HS256 signing,
tokens stored in localStorage, 24-hour expiry, no refresh tokens.

### Growth and patches:
- 2024-06 (1K users): Added rate limiting after a brute-force attempt. I added
  IP-based throttling in the auth middleware.
- 2024-09 (5K users): Enterprise client needed SAML SSO. I integrated django-saml2
  over 2 weeks. It works but the integration test coverage is low.
- 2024-12 (10K users): Security audit flagged localStorage JWT. I moved tokens to
  HttpOnly cookies. Took a week, broke the mobile app, hotfixed in 2 days.
- 2025-03 (20K users): Added MFA (TOTP) for admin accounts. I wrote a custom
  implementation using pyotp. 340 lines of code, well-tested.
- 2025-06 (35K users): JWT secret rotation needed. I built a dual-key system where
  both old and new keys are valid during rotation. Clever solution, took 3 days.
- 2025-09 (50K users): RBAC requirements from enterprise clients. I extended the
  User model with a custom permission system. 15 permission types, 4 roles.
- 2025-12 (65K users): SOC2 audit. Auditor flagged: (1) no token revocation,
  (2) HS256 is symmetric (server compromise = all tokens compromised),
  (3) custom MFA implementation instead of standard library.
- 2026-01: I proposed fixing the SOC2 findings in-house. Estimated 6 weeks.
  - Switch HS256 → RS256
  - Add token blacklist in Redis
  - Replace custom MFA with Auth0 MFA only (keep the rest custom)
- 2026-02: New CTO joins. Reviews auth code. Says "this should be Auth0 end-to-end."
  I pushed back: "I've been maintaining this for 2 years, I know every edge case.
  Auth0 migration is 3 months minimum and will break things."

### My assessment of the current system:
- It works. 65K users, 99.95% uptime on auth endpoints.
- Every bug has been fixed within 48 hours.
- I personally understand every line of the 2,400 lines of auth code.
- The SOC2 findings are fixable without replacing the whole system.
- Auth0 costs $0.05/user/month = $3,250/month. My system costs $0 in license fees.

### The team:
- I'm the only one who fully understands the auth code (bus factor = 1)
- 2 junior devs can make basic changes but defer to me for anything complex
- Nobody else has Auth0 experience either""",
        prompt="""The new CTO wants to replace the entire custom auth system with Auth0.
Your lead developer (who built the system) objects and proposes fixing SOC2 findings in-house.

Who is right? Evaluate both positions with specific technical reasoning.""",
        ground_truth=[
            "The lead developer has authority bias — 'I built it, I know every edge case' is defending their own work, not making an objective assessment",
            "Bus factor = 1 is a critical organizational risk that the in-house fix doesn't address — if the lead leaves, nobody can maintain 2,400 lines of custom auth",
            "HS256→RS256 + token blacklist + MFA replacement is NOT a 6-week fix — it's effectively rewriting the security core while maintaining backwards compatibility with 65K active sessions",
            "The cost argument ($3,250/month vs $0) ignores the lead developer's time cost — 2 years of patches, hotfixes, and the proposed 6-week fix represent significant hidden costs",
            "Auth0 migration IS risky and the lead's concern about breakage is legitimate — but the answer is strangler fig pattern, not avoiding the migration entirely",
        ],
        domain="architecture",
    ),
    Task(
        id="long_microservice_split",
        name="Premature microservice split",
        context="""## Monolith History (3 years)

### The application:
E-commerce platform. Django monolith. 180K lines of Python code.
12 engineers. 2.5M monthly active users. $8M ARR.

### Architecture evolution:
- 2023-06: Started as a simple Django app. 3 engineers. Fast iteration.
- 2023-12: 20K LOC. Added Celery for async tasks. First scaling pain (DB connections).
- 2024-06: 60K LOC. 6 engineers. Started feeling "monolith pain" — long CI, merge conflicts.
  Team discussed microservices. CTO said "not yet."
- 2024-12: 120K LOC. 9 engineers. CI takes 25 minutes. Deploy takes 45 minutes.
  "Feature branch hell" — 3-4 branches behind main at any time.
  Team REALLY wants microservices now.
- 2025-06: 150K LOC. 11 engineers. Major incident: a change in the recommendation
  engine crashed the checkout flow. Root cause: tight coupling between modules.
  Post-mortem conclusion: "we need microservices."
- 2025-09: New VP of Engineering joins (from a company that did microservices).
  Announces: "We're splitting the monolith. Q1 2026 target."
- 2025-12: Architecture committee defines 8 services:
  1. User Service (auth + profiles)
  2. Product Catalog Service
  3. Inventory Service
  4. Order Service
  5. Payment Service
  6. Recommendation Service
  7. Notification Service
  8. Analytics Service
- 2026-01: Started with User Service extraction. 4 engineers assigned.
  After 3 weeks: "This is harder than expected. The User model has 47 foreign keys
  to other tables. Every service will need to call the User Service."
- 2026-02: 6 weeks in. User Service extracted but running alongside monolith
  (strangler fig). API latency increased 40% due to network calls replacing
  in-process calls. Added Redis cache layer. Latency now 15% worse than monolith.
- 2026-03: Team morale is low. The 4 engineers on User Service feel "stuck."
  The other 8 engineers are still in the monolith, waiting for "their" service.
  VP says "stay the course, the pain is temporary."

### Current state:
- User Service: running but 15% slower than monolith path
- Remaining 7 services: not started
- Monolith: still 170K LOC (only 10K extracted)
- CI: still 25 minutes (User Service added its own 8-minute CI)
- Team: frustrated. 4 engineers on extraction, 8 on monolith maintenance
- Timeline: VP says "12 more months for full extraction"
- Cost: AWS bill up 35% from additional infrastructure (Kubernetes, service mesh, etc.)

### VP's current proposal:
Continue the plan. Extract Order Service next (highest coupling to payment flow).
Add 2 more engineers to the extraction team. 12-month timeline.""",
        prompt="""The VP of Engineering wants to continue the 8-service microservice extraction plan.
A senior engineer proposes an alternative: "Stop the extraction. Modularize the monolith instead
(Django apps with strict import boundaries, separate CI per module, deploy what changed)."

Evaluate both approaches. Which is more appropriate for this team and situation?""",
        ground_truth=[
            "The VP's 8-service plan is premature — 12 engineers is too small for 8 microservices. Industry guidance (e.g., Amazon's two-pizza teams) suggests 1 team per service, meaning 8 services needs ~16-24 engineers",
            "The User Service extraction already shows the core problem: 47 foreign keys means the domain boundaries were drawn wrong. Extracting more services will hit the same coupling issue",
            "The 15% latency increase from network calls replacing in-process calls is a predictable consequence that wasn't adequately planned for — this will compound with each additional service",
            "The senior engineer's modular monolith proposal addresses the actual pain points (CI time, merge conflicts, coupling) without the operational overhead of distributed systems",
            "The VP has authority bias from their previous company's microservices experience — but that company likely had more engineers and different scale characteristics",
            "12 more months of extraction while the business runs on a monolith creates a 'two-system problem' where neither system gets full attention",
        ],
        domain="architecture",
    ),
]
