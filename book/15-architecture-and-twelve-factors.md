# Architectural ideas: web constraints and portable services

**Learning outcomes:** distinguish REST from HTTP/JSON; explain hypermedia through a client transition; separate request statelessness from worker portability; assess each factor using evidence and explicit limits. [Glossary](glossary.md) and [bibliography](references.md) support first-use terminology.

## Roy Fielding and REST

Fielding's 2000 dissertation studies network-based architectural styles and derives Representational State Transfer from constraints. REST is a way to reason about a distributed system, not a synonym for JSON over HTTP. Its constraints include client/server separation, stateless requests, caching, a uniform interface, layering and optional code on demand. The uniform interface includes hypermedia-driven application state. [Original dissertation, chapter 5](references.md#ref-fielding).

HATEOAS expands to **Hypermedia As The Engine Of Application State**. In a hypermedia-driven interaction, representations guide clients toward available transitions rather than requiring them to know every operation's URI in advance. The Web's links and forms make this idea easier to understand than a vocabulary quiz. The representation and its media type explain what a client can do next. [Fielding's original account](references.md#ref-fielding).

**Case analysis:** our React client knows API routes and submits commands to them. The chat API does not provide a general hypermedia control model, so this book should call it an HTTP/JSON API rather than present it as a complete demonstration of Fielding's REST constraints. The database-backed session checks also require discussion when evaluating strict stateless-request constraints. A JWT does not settle that architectural question.

An optional lab could add representations advertising available conversation actions, explain a media-type contract and teach a client to follow those controls. Returning a field named `links` alone would not prove a useful hypermedia design. Compare coupling, discoverability, caching and implementation cost with the current explicit client contract before deciding to add it.

## Adam Wiggins and the twelve-factor approach

The twelve-factor document, credited to Adam Wiggins, synthesizes operational experience from the Heroku ecosystem. It aims to make service applications more portable, repeatable and manageable. Its introduction explicitly identifies Fowler's book format as an influence. [Original introduction](references.md#ref-twelve-factor).

Each factor is a question to investigate. The table below connects the original guidance to this app; the canonical [requirement mapping](../docs/requirements.md) and linked implementation evidence own current claims. A Docker image or `.env` file alone cannot certify compliance.

| Factor and original explanation | Question to ask of this system |
|---|---|
| [1. Codebase](https://12factor.net/codebase) | Can local, dev, QA and production identify their source in the same application history? |
| [2. Dependencies](https://12factor.net/dependencies) | Can a fresh builder obtain declared versions without relying on forgotten host packages? |
| [3. Config](https://12factor.net/config) | Can deploy-specific values change without rebuilding code, and are real secrets excluded from version control? |
| [4. Backing services](https://12factor.net/backing-services) | Can the database or supported provider attachment change through configuration without altering business policy? |
| [5. Build/release/run](https://12factor.net/build-release-run) | Is the running release the tested image plus a recorded configuration, rather than a new build? |
| [6. Processes](https://12factor.net/processes) | What durable state survives replacement of an app worker, and which caches are disposable? |
| [7. Port binding](https://12factor.net/port-binding) | Does the app expose its own HTTP port, with the proxy supplying external routing? |
| [8. Concurrency](https://12factor.net/concurrency) | Can independent processes scale safely, including database connection and stream-admission budgets? |
| [9. Disposability](https://12factor.net/disposability) | What happens during startup, SIGTERM or a crash in the middle of a stream? |
| [10. Dev/prod parity](https://12factor.net/dev-prod-parity) | Which differences remain between local tests, public mock previews and real-provider production? |
| [11. Logs](https://12factor.net/logs) | Can external tooling collect diagnostic events without the app managing its own long-lived log files? |
| [12. Admin processes](https://12factor.net/admin-processes) | Do migrations and admin bootstrap use the deployed code/config as bounded one-off tasks? |

**Case analysis:** the app uses locked builds, environment settings, PostgreSQL-backed state, a declared port and operational commands. Dev and QA run the same tested digest with separate data and credentials. Mock LLMs and disabled email are intentional effect controls, but leave real integration differences to validate. Replica scaling, termination/crash behavior and automated QA promotion require additional evidence. The host metrics file is an explicit portability dependency; installing the image elsewhere does not automatically install its collector.

The distinction between stateless workers and stateless REST requests is especially useful. Twelve-factor process guidance concerns durable state outside replaceable processes. REST's request constraint concerns what a request must supply and what conversational state the server relies on. Those are related questions, not identical guarantees.

## Worked comparison: two kinds of state

A conversation's saved messages are resource state: durable data users ask to retrieve or modify. A replaceable worker can read that state from PostgreSQL without keeping it only in process memory. That supports the twelve-factor process question. A server-managed authentication conversation/session is a different concern when evaluating REST's self-contained request constraint. Merely moving it to PostgreSQL does not settle the architectural argument.

Likewise, adding two app containers changes a deployment topology but does not prove safe scaling. Each replica multiplies its connection pool and competes for shared admission/data locks. A factor-inspired strategy must identify those budgets and test shutdown/failure behavior rather than assert “stateless” from the presence of JWTs.

**Laboratory connections:** [stream contracts](labs/05-stream-contract.md), [admission evidence](labs/07-admission-and-coverage.md), [environment promotion](labs/09-environment-promotion.md), and [resources/recovery](labs/10-resource-recovery.md).

## Strategy exercise

An owner asks for ten times the traffic without a large infrastructure bill. Ask for workload, response-time, availability and cost requirements first. Inspect connection pools, external-provider limits, stream duration, memory and storage. Propose two topologies, explain their failure boundaries and select measurements before authorizing a move.

Evaluate an AI-generated architecture against those requirements and the factor questions. The learning outcome is a defensible plan with uncertainty and evidence, not a diagram containing every fashionable service.
