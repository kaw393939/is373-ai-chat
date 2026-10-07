# Project hub

Build an understandable, secure AI chat system that solves a useful business problem and can be operated by another engineer.

| Question | Canonical location |
|---|---|
| What are we building and teaching? | [Baseline](baseline.md): stable requirement IDs and lesson map |
| What work is outstanding, active or blocked? | [GitHub issues](https://github.com/kaw393939/is373-ai-chat/issues): status labels, acceptance criteria and milestones |
| How do we deliver and review work? | [Working agreement](working-agreement.md): readiness, Done and atomic commits |
| How do I find the initial issues? | [Backlog index](backlog.md): links and dependencies; no duplicated status |
| What actually passed or shipped? | [Implementation evidence](../implementation-evidence.md), linked CI runs and release identities |
| Why did we choose this architecture? | [Architecture](../architecture.md), [research decisions](../references-and-decisions.md) and issue-linked ADRs for new consequential decisions |
| How do I learn the tools? | [Book and laboratory map](../../book/README.md) |
| How ready is the textbook for publication? | [Dated editorial review](../editorial/2026-10-06-publisher-review.md): findings, reader promise and revision priorities |
| What changed after the publisher review? | [Development-edition evidence](../../book/evidence/2026-10-06-revision.md), [instructor pack](../../book/instructor/README.md) and [edition identities](../../book/edition.md) |

Docs define durable intent and explanation. Issues own item-specific acceptance criteria and live progress. Commits/PRs own changes. Tests and release records own evidence. Link between these; do not copy mutable progress into another spreadsheet or document.

Start at the [baseline](baseline.md), then take the highest-priority unblocked issue in the [live ready queue](https://github.com/kaw393939/is373-ai-chat/issues?q=is%3Aissue%20is%3Aopen%20label%3Astatus%3Aready). The initial backlog is an ordered proposal, not a time-boxed sprint commitment. No GitHub Projects board is required to read or maintain it.

[ADR 0001](../decisions/0001-environments-and-releases.md) proposes isolated dev/QA/prod and semantic releases. Issues own implementation and acceptance. Public dev and QA are deployed; automated promotion remains open. See the [environment evidence](../environments.md).
