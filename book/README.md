# From Request to Release

## A software engineering book with a working AI chat laboratory

This book studies how people build useful software that survives change. The chat application is our continuing case study: a user need becomes an interface, an authenticated request, a transaction, an external integration, a tested artifact and an operated service. Tools matter because they change that journey. We study their origins, alternatives and limitations alongside their APIs.

Start with [how to read the code](00-reading-code.md), [the historical foundations](12-history.md) and [the people and ideas](13-engineering-ideas.md). Continue with [Agile and its seventeen signatories](14-agile-and-community.md), [Fielding/REST/HATEOAS and twelve-factor design](15-architecture-and-twelve-factors.md), and [human judgment, Bloom's taxonomy and AI](16-human-judgment-and-ai.md). Then follow the eleven technical chapters listed in the [repository index](../README.md#read-the-textbook). Readers who need a working installation first can start with [local development](02-local.md) and return to the historical material afterward.

The [October 6 publisher-style review](../docs/editorial/2026-10-06-publisher-review.md) assesses the manuscript's strengths, publication gaps and next revision tranche against a fixed source snapshot. Issues continue to own live progress.

## Four connected parts

| Part | Questions | Chapters and practice |
|---|---|---|
| Foundations | Why did these tools and practices emerge? How do we judge a design? | Reading code, history, engineering ideas, whole-system request trace |
| Build a useful system | How do data, identity, interfaces and integrations cooperate? | Local development, migrations, authentication, streaming, email and usability |
| Deliver and operate | How does a change reach users and survive failure? | Testing, delivery, hosting, limits, monitoring and recovery |
| Exercise engineering judgment | What should change, what evidence is sufficient, and what is the business consequence? | Labs, issue-based capstones, tradeoff reviews and incident explanations |

The existing technical chapters are concise foundations, not finished comprehensive chapters. Expansion must add a historical problem, a worked explanation, a concrete alternative, a linked code tour, a lab and a discussion of limits. The new foundation chapters and first lab establish that format. The lab map below identifies authored material separately from planned work; it is not a claim that every lab has been written or classroom-tested.

## Laboratory map

| Lab | Learn by doing | Canonical lesson | Material |
|---|---|---|---|
| 01 | Explain and test JWT validation; distinguish identity from authority | [Identity](04-auth.md) | [Authored pilot](labs/01-token-boundaries.md); second-reader assessment pending |
| 02 | Reproduce locally and trace a request | [Local](02-local.md), [system](01-system.md) | Planned full lab; existing chapter exercises |
| 03 | Add a compatible database migration and review SQL | [Data](03-data.md) | Planned full lab |
| 04 | Register two users and prove ownership/role boundaries | [Identity](04-auth.md) | Planned full lab |
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
