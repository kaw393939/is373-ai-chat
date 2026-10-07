# From Request to Release

## A software engineering book with a working AI chat laboratory

This book studies how people build useful software that survives change. The chat application is our continuing case study: a user need becomes an interface, an authenticated request, a transaction, an external integration, a tested artifact and an operated service. Tools matter because they change that journey. We study their origins, alternatives and limitations alongside their APIs.

Start with [the reader's guide](start-here.md): audience, entry skills, equipment, costs, readiness and routes through the book. Use [the foundations bridge](foundations.md) to repair a specific gap before a chapter assumes it. The intended reader can already write a small program; this book develops whole-system reasoning rather than teaching programming from the first statement.

The [October 6 publisher-style review](../docs/editorial/2026-10-06-publisher-review.md) assesses the manuscript's strengths, publication gaps and next revision tranche against a fixed source snapshot. Issues continue to own live progress.

## One course, four connected parts

Follow the rows in order for the full course. File prefixes identify stable documents; they are not a second course sequence. Labs revisit earlier concepts as the learner acquires more evidence.

| Part / sequence | Reading | Question or practice |
|---|---|---|
| I · Origins and ideas · 1 | [Read code as an argument](00-reading-code.md) | What claim does a function make, and where is its evidence? |
| 2 | [Historical foundations](12-history.md) | Which persistent problems shaped this stack? |
| 3 | [People and engineering ideas](13-engineering-ideas.md) | Which ideas clarify a design choice? |
| 4 | [Agile and its community](14-agile-and-community.md) | How do people coordinate feedback and change? |
| 5 | [REST/HATEOAS and twelve-factor design](15-architecture-and-twelve-factors.md) | Which constraints does the current system actually demonstrate? |
| II · Build a useful system · 6 | [Trace the whole system](01-system.md) | Read the conceptual journey; return for Lab 02 after setup. |
| 7 | [Local development](02-local.md) | Reproduce the controlled learning environment and execute the trace. |
| 8 | [Data and migrations](03-data.md) | Preserve data while software changes; Lab 03. |
| 9 | [Identity and roles](04-auth.md) | Distinguish identity, current authority and ownership; Labs 01/04. |
| 10 | [Streaming and adapters](05-streaming.md) | Reason about incremental results, cancellation and failure. |
| 11 | [Transactional email](11-email.md) | Connect a transaction to an external delivery system. |
| III · Deliver and operate · 12 | [Testing with purpose](07-testing.md) | Select evidence that addresses a real failure. |
| 13 | [Build, release and deploy](08-delivery.md) | Trace a tested artifact to a running release. |
| 14 | [Hosting](09-hosting.md) | Explain DNS, HTTPS, configuration and installation boundaries. |
| 15 | [Limits and monitoring](06-operations.md) | Connect resource ceilings, symptoms and user consequences. |
| 16 | [Recovery](10-recovery.md) | Diagnose interruption and recover durable state. |
| IV · Exercise judgment · 17 | [Human judgment and AI](16-human-judgment-and-ai.md) | Evaluate alternatives and deliver a justified capstone. |

This is a developing manuscript. Local development, data and identity provide expanded sample chapters; several later technical chapters remain concise foundations. Each completed chapter needs a motivating problem, historical context, a worked explanation, alternatives, a linked code tour, observable evidence and discussion of limits. Authored pages are distinct from independently validated teaching material. Consult each lab's verification statement rather than infer readiness from its place in this contents list.

For an installation-first route, read [local development](02-local.md) → [whole system](01-system.md) → [identity](04-auth.md), perform Labs 02 and 01, then return to Part I. For an experienced engineer's review route, inspect the [code-reading tour](00-reading-code.md), [data](03-data.md), [identity](04-auth.md), [twelve-factor case analysis](15-architecture-and-twelve-factors.md) and [delivery](08-delivery.md). The [reader's guide](start-here.md) explains what each route assumes.

## Laboratory map

| Lab | Learn by doing | Canonical lesson | Material |
|---|---|---|---|
| 01 | Explain and test JWT validation; distinguish identity from authority | [Identity](04-auth.md) | [Authored pilot](labs/01-token-boundaries.md); second-reader assessment pending |
| 02 | Trace an in-process ASGI request and temporary persisted state | [System](01-system.md), [code reading](00-reading-code.md) | [Request-trace lab](labs/02-request-trace.md); no Docker/browser/proxy proof |
| 03 | Generate an additive index migration and scoped drift check | [Data](03-data.md) | [Migration lab](labs/03-migration.md); SQLite guided fixture, PostgreSQL transfer pending |
| 04 | Register two users and prove ownership/role boundaries | [Identity](04-auth.md) | [Ownership lab](labs/04-ownership.md); consult its verification statement |
| 05 | Fragment a stream, cancel it and diagnose a provider failure | [Streaming](05-streaming.md) | Planned full lab |
| 06 | Improve keyboard access and diagnose a stale UI result | [Testing](07-testing.md) | Planned full lab; implementation issues #9 and #19 |
| 07 | Race admission requests and assess coverage evidence | [Testing](07-testing.md), [limits](06-operations.md) | Planned full lab |
| 08 | Trace a tested image through registry and deployment | [Delivery](08-delivery.md) | Planned full lab |
| 09 | Demonstrate environment isolation and candidate promotion | [Environment runbook](../docs/environments.md) | Planned full lab; promotion implementation #24 remains open |
| 10 | Diagnose resource pressure and restore a disposable database | [Operations](06-operations.md), [recovery](10-recovery.md) | Planned full lab; independent recovery proof pending |
| 11 | Exercise outbox retries and explain email authentication | [Email](11-email.md) | Planned full lab; real sending activation #3 remains open |
| 12 | Deliver a justified improvement with issue/commit/test evidence | [Working agreement](../docs/project/working-agreement.md) | Planned capstone; [baseline](../docs/project/baseline.md) defines capabilities |

Every full lab follows: problem → objectives → prerequisites and environment → guided investigation → controlled failure → smallest justified repair → acceptance evidence → reflection → optional extension. Estimate learner time only after a pilot, rather than inventing reliable completion times.

Failures and destructive exercises run in a learner-owned disposable local environment. Shared dev/QA are coordinated acceptance environments; production is an observation target only when the exercise explicitly permits a read-only check. Public URLs and public fixture passwords are never interchangeable with private credentials.

## Assessment and sources

Assess explanation, reproduction, diagnosis, change and evidence. A learner should identify what a test cannot prove and explain one rejected alternative. AI assistance is permitted: the learner remains responsible for reviewing generated code, tracing authorization/data boundaries and defending the result. T-shaped learning means breadth across the system plus depth in one selected layer, not memorizing every tool's options.

Historical dates and attributed ideas link primary publications, author accounts or official project histories beside the claim. Separate an author's contribution from our application of it. Avoid claims that one person invented a whole practice, that every team used one earlier approach, or that newer technology eliminates older choices. This book paraphrases and links original work; it does not reproduce copyrighted books.

Durable educational scope lives here and in [REQ-LEARNING](../docs/project/baseline.md#req-learning). [Book/course #26](https://github.com/kaw393939/is373-ai-chat/issues/26) owns expansion acceptance; [teaching-evidence audit #23](https://github.com/kaw393939/is373-ai-chat/issues/23) owns claim corrections and independent reader assessment. Issues own detailed acceptance and live progress; chapters link source and evidence. Commands are reviewed against the current repository and labeled when operational or second-reader verification is still pending.

## Reference and teaching material

Use the [glossary](glossary.md) for vocabulary, [source ledger](references.md) for attribution, [generated code tours](generated/code-tours.md) for small excerpts and the [instructor guide](instructor/README.md) for assessment. [Edition records](edition.md) identify the manuscript/source relationship. [Publication guidance](publication.md) explains the book build, licenses and release checks. A successful site build is a presentation check; it is not independent learner validation.
