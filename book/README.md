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

This is a developing manuscript with worked technical lessons and twelve authored labs. The lessons connect motivating problems, history, worked explanations, alternatives, code tours and evidence; continued editorial development and independent reader testing remain necessary. Authored pages are distinct from validated teaching material. Some container exercises are still unexecuted on this workstation, and advanced product capabilities remain open. Consult each lab's verification statement rather than infer readiness from its place in this contents list.

For an installation-first route, read [local development](02-local.md) → [whole system](01-system.md) → [identity](04-auth.md), perform Labs 02 and 01, then return to Part I. For an experienced engineer's review route, inspect the [code-reading tour](00-reading-code.md), [data](03-data.md), [identity](04-auth.md), [twelve-factor case analysis](15-architecture-and-twelve-factors.md) and [delivery](08-delivery.md). The [reader's guide](start-here.md) explains what each route assumes.

## Laboratory map

| Lab | Learn by doing | Canonical lesson | Material |
|---|---|---|---|
| 01 | Explain and test JWT validation; distinguish identity from authority | [Identity](04-auth.md) | [Authored pilot](labs/01-token-boundaries.md); second-reader assessment pending |
| 02 | Trace an in-process ASGI request and temporary persisted state | [System](01-system.md), [code reading](00-reading-code.md) | [Request-trace lab](labs/02-request-trace.md); no Docker/browser/proxy proof |
| 03 | Generate an additive index migration and scoped drift check | [Data](03-data.md) | [Migration lab](labs/03-migration.md); SQLite guided fixture, PostgreSQL transfer pending |
| 04 | Prove ownership/roles using temporary synthetic accounts | [Identity](04-auth.md) | [Ownership lab](labs/04-ownership.md); scoped integration checks and a teaching mutant |
| 05 | Decode fragmented Unicode and diagnose missing stream completion | [Streaming](05-streaming.md) | [Stream-contract lab](labs/05-stream-contract.md); contained fake transport |
| 06 | Exercise browser journeys and evaluate keyboard access | [Testing](07-testing.md) | [Browser/accessibility lab](labs/06-browser-accessibility.md); transfer and human assistive-technology review pending |
| 07 | Race admission requests and challenge a coverage number | [Testing](07-testing.md), [limits](06-operations.md) | [Admission/coverage lab](labs/07-admission-and-coverage.md); consult PostgreSQL wrapper execution status |
| 08 | Compare local image identity with the CI release path | [Delivery](08-delivery.md) | [Image-delivery lab](labs/08-image-delivery.md); local Docker activity unverified here; no push/deploy |
| 09 | Inspect isolation and model an accepted promotion | [Environment runbook](../docs/environments.md) | [Environment/promotion lab](labs/09-environment-promotion.md); a decision model, actual promotion #24 remains open |
| 10 | Rehearse disposable restore and diagnose stale metrics | [Operations](06-operations.md), [recovery](10-recovery.md) | [Resource/recovery lab](labs/10-resource-recovery.md); Docker wrapper unverified here; off-host proof pending |
| 11 | Test mocked outbox retries, retention and verification | [Email](11-email.md) | [Email-outbox lab](labs/11-email-outbox.md); actual sending activation #3 remains open |
| 12 | Deliver a justified stream-contract improvement and evidence | [Working agreement](../docs/project/working-agreement.md) | [Strategy capstone](labs/12-strategy-capstone.md); private learner repair and defended decision |

Every full lab follows: problem → objectives → prerequisites and environment → guided investigation → controlled failure → smallest justified repair → acceptance evidence → reflection → optional extension. Estimate learner time only after a pilot, rather than inventing reliable completion times.

Begin with the [laboratory preflight](labs/README.md). Labs 01–05 can investigate temporary or in-process examples without Docker; image, PostgreSQL concurrency, Compose and restore activities have distinct container prerequisites and execution limits. An authored laboratory map does not imply that all infrastructure exercises or learner transfer solutions have passed.

Failures and destructive exercises run in a learner-owned disposable local environment. Shared dev/QA are coordinated acceptance environments; production is an observation target only when the exercise explicitly permits a read-only check. Public URLs and public fixture passwords are never interchangeable with private credentials.

## Assessment and sources

Assess explanation, reproduction, diagnosis, change and evidence. A learner should identify what a test cannot prove and explain one rejected alternative. AI assistance is permitted: the learner remains responsible for reviewing generated code, tracing authorization/data boundaries and defending the result. T-shaped learning means breadth across the system plus depth in one selected layer, not memorizing every tool's options.

Historical dates and attributed ideas link primary publications, author accounts or official project histories beside the claim. Separate an author's contribution from our application of it. Avoid claims that one person invented a whole practice, that every team used one earlier approach, or that newer technology eliminates older choices. This book paraphrases and links original work; it does not reproduce copyrighted books.

Durable educational scope lives here and in [REQ-LEARNING](../docs/project/baseline.md#req-learning). [Book/course #26](https://github.com/kaw393939/is373-ai-chat/issues/26) owns expansion acceptance; [teaching-evidence audit #23](https://github.com/kaw393939/is373-ai-chat/issues/23) owns claim corrections and independent reader assessment. Issues own detailed acceptance and live progress; chapters link source and evidence. Commands are reviewed against the current repository and labeled when operational or second-reader verification is still pending.

## Reference and teaching material

Use the [glossary](glossary.md) for vocabulary, [source ledger](references.md) for attribution, [generated code tours](generated/code-tours.md) for small excerpts and the [instructor guide](instructor/README.md) for assessment. [Edition records](edition.md) identify the manuscript/source relationship. [Publication guidance](publication.md) explains the book build, licenses and release checks. A successful site build is a presentation check; it is not independent learner validation.
