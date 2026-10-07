# Product and educational baseline

Baseline date: October 6, 2026. Released source: `d65a19c8d3cd344d31b8f01103fe5e3137a8485d`; schema `0002`. [Release evidence](../implementation-evidence.md) records image, tests and observed production behavior. This baseline is a reference point, not a promise that subsequent issues are complete.

## Product goal

An operator can install and maintain a secure, provider-independent text-chat application on DigitalOcean at firehose360.com. Users register, receive approval, sign in, stream replies and manage private conversations. Administrators enforce budgets and see system health. Another engineer can reproduce the installation from the repository.

Favor a comprehensible modular monolith, bounded costs and useful change boundaries. Use SOLID, typed contracts, adapter/strategy, explicit transactions and the outbox where they solve a demonstrated problem. SQLAlchemy already supplies a unit of work. Pattern counts, class counts and coverage percentages are not acceptance evidence.

## Canonical capability map

Issue bodies reference these anchors and own the detailed acceptance criteria. Keep IDs stable; add a new ID for a new capability.

| ID | Requirement and baseline status | Learn and inspect |
|---|---|---|
| <a id="req-identity"></a>REQ-IDENTITY | Registration, approval, JWT/refresh, ownership and roles are released. Administrator MFA and multi-tab refresh coordination remain open. | [Identity](../../book/04-auth.md), [routes](../../app/main.py), [security](../../app/security.py) |
| <a id="req-chat"></a>REQ-CHAT | Text streaming, saved history, title search, CRUD, stop/retry and safe Markdown are released. Typed terminal-event semantics, stale UI results and pagination need work. | [Streaming](../../book/05-streaming.md), [providers](../../app/providers.py), [services](../../app/services.py) |
| <a id="req-email"></a>REQ-EMAIL | Encrypted outbox and verification/recovery are implemented and tested. Production sending is disabled until sender/DNS activation and real inbox proof. Existing Google inbox receives replies; no additional paid mailbox is required. | [Email](../../book/11-email.md), [activation status](../email-options.md) |
| <a id="req-operations"></a>REQ-OPERATIONS | Compose, HTTPS, resource ceilings, metrics and daily local dumps are released. Off-host recovery, cloud account settings and fresh-host proof remain open. | [Operations](../../book/06-operations.md), [hosting](../../book/09-hosting.md), [recovery](../../book/10-recovery.md) |
| <a id="req-delivery"></a>REQ-DELIVERY | CI builds once, browser-tests/scans the image and deploys its digest. Migrations and schema-aware recovery exist; setup-failure recovery and termination behavior need additional proof. | [Delivery](../../book/08-delivery.md), [workflow](../../.github/workflows/delivery.yml), [operator wrapper](../../deploy/chat-deploy) |
| <a id="req-quality"></a>REQ-QUALITY | The original release passed 46 PostgreSQL tests and three image browser journeys; the guarded revision passed 59 PostgreSQL tests and three image browser journeys. Measured Python app line/branch coverage is 100% with documented exclusions. This is targeted validation, not exhaustive security assurance. | [Testing](../../book/07-testing.md), [revision evidence](../../book/evidence/2026-10-06-revision.md), [review](../review-and-security.md) |
| <a id="req-architecture"></a>REQ-ARCHITECTURE | Provider adapters, injected construction, database-backed state and outbox exist. Frontend lifecycle ownership, transport boundaries, transaction contracts and stronger types need refinement. | [Whole system](../../book/01-system.md), [models/migrations](../../book/03-data.md) |
| <a id="req-privacy"></a>REQ-PRIVACY | Private ownership and protected configuration are enforced; remote Markdown images are omitted. Retention/export/account deletion policy is not yet specified. | [Auth](../../book/04-auth.md), [review](../review-and-security.md) |
| <a id="req-learning"></a>REQ-LEARNING | Teach T-shaped engineering: depth in one layer, enough breadth to explain a request across UI/API/database/provider/deployment. Learners must explain, test, diagnose and modify AI-generated work. Fresh-reader and fresh-server assessments remain open. | [Local setup](../../book/02-local.md), [lesson index](../../README.md#read-the-textbook) |

## Architecture and twelve-factor evidence

[Requirements](../requirements.md) remains the canonical factor/pattern mapping. Evaluate intent separately from proof: process scaling, stream termination/crashes, staging parity and host-metrics portability are not fully demonstrated. The PostgreSQL fallback tests cannot establish PostgreSQL lock behavior. JWTs alone do not make a process stateless; durable session state resides in the backing database.

## Scope boundaries

One amd64 server, one app process, conservative reservation units rather than dollar billing, and short release interruption. Unfixed OS advisories are recorded in release evidence. Real email, replacement provider credentials and independent recovery are readiness work, not optional extensions.

Attachments, retrieval/RAG, tools, voice, sharing and billing are discovery topics after readiness. A separate proposal must identify the user/business value, data/authorization boundary, costs and measurable acceptance criteria before implementation. No speculative feature is counted as delivered.

## Educational assessment

For an issue, the learner must (1) explain its business consequence, (2) trace the relevant request/data flow, (3) reproduce the failure safely, (4) implement the smallest justified change, and (5) demonstrate acceptance with tests or operational evidence. One exercise should require diagnosing a failed deployment or integration rather than merely producing a screen.

Use [working agreement](working-agreement.md) for delivery mechanics and the issue for the current acceptance criteria. Correct explanations in the relevant lesson when implementation changes.

## Comprehensive book direction

[From Request to Release](../../book/README.md) defines the educational structure: readable annotated code, historical alternatives, the people behind the ideas, full labs and judgment-focused assessment. Include the twelve factors, Agile Manifesto and all original signatories, Fowler/Martin and other engineering contributors, Guido van Rossum and Python, Torvalds and Linux/Git, Fielding and REST/HATEOAS, and containerization. Connect each story to design criteria and the current case study; do not claim every principle is fully implemented. Use revised Bloom objectives to assess remembering/understanding/applying/analyzing/evaluating/creating, with AI-assisted implementation subject to human explanation, verification and strategy. Authored material and independent learner validation are distinct evidence.
