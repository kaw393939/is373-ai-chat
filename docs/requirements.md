# Requirements and implementation acceptance

This checklist began as the design scope. The implemented core and executed checks are recorded in [implementation evidence](implementation-evidence.md). Email delivery activation, advanced features and independent fresh-droplet verification remain follow-up work. The [project baseline](project/baseline.md) owns scope and stable capability IDs; [GitHub issues](https://github.com/kaw393939/is373-ai-chat/issues) own live acceptance criteria and status.

## Twelve-factor mapping

| Factor | Implementation requirement | Evidence |
|---|---|---|
| Codebase | One app repository, multiple independently configured deployments | Commit identity in deployed release |
| Dependencies | Declare and lock backend/frontend dependencies; isolated builds | Frozen dependency installs |
| Config | Validated deploy-specific runtime config; ignored local .env | Same image runs with separate configs |
| Backing services | Database and LLM providers through configuration/interfaces | Substitute test services/adapters |
| Build/release/run | Build once; release combines digest/config; run consumes it | Tested digest equals deployed digest |
| Processes | Stateless app workers; durable sessions/chat in database | Restart preserves account/chat state |
| Port binding | HTTP service on a declared internal port | Works locally and behind existing proxy |
| Concurrency | Bounded async generation; separate app/worker processes where needed | Concurrent-user tests and shared limits |
| Disposability | Fast readiness and graceful shutdown with interrupted-run handling | Controlled stop during streaming |
| Dev/prod parity | PostgreSQL and same application contracts across environments | Container integration tests |
| Logs | JSON response-start records with generated request IDs; exclude bodies, headers and query values | Operational logs without credentials |
| Admin processes | Migrations, first-admin bootstrap, backups as one-off tasks | Reproducible documented commands |

Mapping adapted to this proposed app from [The Twelve-Factor App](https://12factor.net/). This table is a design checklist, not a compliance certification.

## SOLID and useful patterns

| Principle or pattern | Concrete use |
|---|---|
| Single responsibility | Primary concerns are grouped in routes/use cases/providers; UI and backend boundary refinement remains #16/#17 |
| Open/closed | Add a provider adapter without changing chat orchestration |
| Liskov substitution | Normalization and selected error tests provide partial evidence; complete shared terminal/cancellation semantics remain #12/#18 |
| Interface segregation | The current chat port exposes streaming; embeddings/tool/image capabilities and their contracts are not implemented |
| Dependency inversion | Generation receives a provider; use cases still directly depend on SQLAlchemy models and some FastAPI errors (#17) |
| Adapter and strategy | Normalize provider APIs and select models from validated configuration |
| Unit of work | Short explicit database transactions; clear commit/rollback ownership |
| State machine | Generation statuses exist; centralized transition enforcement and complete provider terminal-event contracts remain follow-up work (#12/#17/#18), not a fully proved pattern |
| Policy | Server-enforced roles, ownership, budgets, and model eligibility |

Avoid one class per trivial operation and unnecessary microservices. The transactional email outbox now provides durable asynchronous delivery; add a separate queue only for a demonstrated additional need. Architecture review should assess actual responsibilities and change costs, not pattern counts.

## Milestones

1. **Architecture decisions:** frontend, initial providers, registry, hostname, registration policy, initial roles, application feature scope, and production/staging topology.
2. **Runnable foundation:** locked environments, FastAPI/UI, PostgreSQL, SQLAlchemy, Alembic, Compose, .env examples, mock provider, health endpoints, and local instructions.
3. **Accounts and admin:** registration, verification/reset email, JWT/refresh lifecycle, roles, session revocation, admin bootstrap and console, audit trail, account abuse controls.
4. **Chat:** owned conversation history, model selection, streaming, cancellation/retry, deterministic provider adapter tests, usage/budget controls, safe Markdown rendering.
5. **Delivery:** exact-image CI tests, registry publication, controlled migrations, digest deployment, public verification, explicit application rollback limits.
6. **Operations and teaching guide:** fresh-server and existing-server paths, backups/restoration, monitoring, failure exercises, restart/load checks, student explanation and evidence.
7. **Advanced features:** scope attachments/RAG/tools/sharing/voice/billing independently after the core is verified.

## Core acceptance criteria

- ACC-01: A fresh local checkout starts using the guide with PostgreSQL and mock streaming, without a paid provider key.
- ACC-02: An anonymous user can register and receive administrator approval; recovery, logout, and session revocation behave as specified.
- ACC-03: Invalid/expired JWTs fail; refresh reuse revokes the affected session family; users cannot self-promote.
- ACC-04: Users cannot access another user's conversations by guessed IDs; admin privileges are enforced by the API.
- ACC-05: Chat streams incrementally through production HTTPS, survives arbitrary chunk boundaries, and reports completion/errors/cancellation correctly.
- ACC-06: At least two provider adapters satisfy shared core contracts; unsupported capabilities are clear. Paid-provider verification is recorded separately from mock tests.
- ACC-07: Reviewed migrations work on an empty DB and a prior release schema; CI detects model/schema drift.
- ACC-08: Failed checks prevent publication/deployment; production runs the exact tested digest and exposes the expected commit/schema readiness.
- ACC-09: Failed migration stops release; compatible app rollback works and incompatible rollback is explicitly rejected/documented.
- ACC-10: No committed runtime secrets or secret-bearing images/logs; database and admin operational interfaces have intended exposure.
- ACC-11: Backup restoration is exercised; restarts preserve state; observed memory/concurrency limits are documented.
- ACC-12: Fresh-server installation and the existing-Traefik integration are independently verified and understandable to students.
