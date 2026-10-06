# Initial backlog index

Reviewed October 6, 2026 against release `d65a19c8d3cd344d31b8f01103fe5e3137a8485d`. This is a navigation/dependency index, not a second status or acceptance-criteria store. GitHub issues own current priority, milestone, status and acceptance criteria; priorities below describe the initial ordering only.

## Live views

- [Ready](https://github.com/kaw393939/is373-ai-chat/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22status%3Aready%22)
- [Blocked](https://github.com/kaw393939/is373-ai-chat/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22status%3Ablocked%22)
- [In progress](https://github.com/kaw393939/is373-ai-chat/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22status%3Ain-progress%22)
- [Time critical](https://github.com/kaw393939/is373-ai-chat/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22priority%3AP0%22)
- [All outstanding work](https://github.com/kaw393939/is373-ai-chat/issues?q=is%3Aissue%20is%3Aopen)

[Milestone goals](https://github.com/kaw393939/is373-ai-chat/milestones) provide production-readiness, correctness/architecture and learning views. No due dates or owners have been invented.

## Work items

| Initial priority | Issue | Canonical requirement | Prerequisites |
|---|---|---|---|
| P0 | [#2 · Replace the temporary provider credential and prove continuity](https://github.com/kaw393939/is373-ai-chat/issues/2) | [REQ-OPERATIONS](baseline.md#req-operations) | See issue for access needs |
| P1 | [#3 · Activate transactional email and prove the real account lifecycle](https://github.com/kaw393939/is373-ai-chat/issues/3) | [REQ-EMAIL](baseline.md#req-email) | See issue for access needs |
| P1 | [#4 · Add encrypted off-host backups and restore the current release](https://github.com/kaw393939/is373-ai-chat/issues/4) | [REQ-OPERATIONS](baseline.md#req-operations) | See issue for access needs |
| P1 | [#5 · Verify cloud network controls and actionable operational alerts](https://github.com/kaw393939/is373-ai-chat/issues/5) | [REQ-OPERATIONS](baseline.md#req-operations) | See issue for access needs |
| P1 | [#6 · Protect administrator access with MFA and recovery procedures](https://github.com/kaw393939/is373-ai-chat/issues/6) | [REQ-IDENTITY](baseline.md#req-identity) | See issue for access needs |
| P1 | [#7 · Rehearse installation from a clean checkout on a fresh host](https://github.com/kaw393939/is373-ai-chat/issues/7) | [REQ-LEARNING](baseline.md#req-learning) | [#4](https://github.com/kaw393939/is373-ai-chat/issues/4) |
| P1 | [#8 · Prove multi-replica limits and stream/email termination behavior](https://github.com/kaw393939/is373-ai-chat/issues/8) | [REQ-DELIVERY](baseline.md#req-delivery) | See issue for access needs |
| P1 | [#9 · Prevent stale conversation and streaming results after navigation or logout](https://github.com/kaw393939/is373-ai-chat/issues/9) | [REQ-CHAT](baseline.md#req-chat) | See issue for access needs |
| P1 | [#10 · Coordinate refresh rotation across tabs and logout](https://github.com/kaw393939/is373-ai-chat/issues/10) | [REQ-IDENTITY](baseline.md#req-identity) | See issue for access needs |
| P1 | [#11 · Require explicit disposable targets before destructive test setup](https://github.com/kaw393939/is373-ai-chat/issues/11) | [REQ-QUALITY](baseline.md#req-quality) | See issue for access needs |
| P1 | [#12 · Reject truncated provider streams and interpret terminal reasons](https://github.com/kaw393939/is373-ai-chat/issues/12) | [REQ-CHAT](baseline.md#req-chat) | See issue for access needs |
| P1 | [#13 · Make deployment setup failures recoverable before promotion](https://github.com/kaw393939/is373-ai-chat/issues/13) | [REQ-DELIVERY](baseline.md#req-delivery) | See issue for access needs |
| P1 | [#14 · Preserve an active administrator under concurrent access edits](https://github.com/kaw393939/is373-ai-chat/issues/14) | [REQ-IDENTITY](baseline.md#req-identity) | See issue for access needs |
| P1 | [#24 · Introduce isolated dev, QA and production digest promotion](https://github.com/kaw393939/is373-ai-chat/issues/24) | [REQ-DELIVERY](baseline.md#req-delivery) | Topology/access decision |
| P1 | [#25 · Establish semantic release versions and linked release evidence](https://github.com/kaw393939/is373-ai-chat/issues/25) | [REQ-DELIVERY](baseline.md#req-delivery) | [#24](https://github.com/kaw393939/is373-ai-chat/issues/24) |
| P2 | [#15 · Make email/account outcomes consistent across quota and approval order](https://github.com/kaw393939/is373-ai-chat/issues/15) | [REQ-EMAIL](baseline.md#req-email) | Mock delivery; no issue dependency |
| P2 | [#16 · Separate frontend screens from session and conversation lifecycle](https://github.com/kaw393939/is373-ai-chat/issues/16) | [REQ-ARCHITECTURE](baseline.md#req-architecture) | [#9](https://github.com/kaw393939/is373-ai-chat/issues/9), [#10](https://github.com/kaw393939/is373-ai-chat/issues/10) |
| P2 | [#17 · Clarify backend use cases, policies and transaction ownership](https://github.com/kaw393939/is373-ai-chat/issues/17) | [REQ-ARCHITECTURE](baseline.md#req-architecture) | [#14](https://github.com/kaw393939/is373-ai-chat/issues/14), [#12](https://github.com/kaw393939/is373-ai-chat/issues/12) |
| P2 | [#18 · Define typed provider, SSE and admin response contracts](https://github.com/kaw393939/is373-ai-chat/issues/18) | [REQ-ARCHITECTURE](baseline.md#req-architecture) | [#12](https://github.com/kaw393939/is373-ai-chat/issues/12) |
| P2 | [#19 · Make account and conversation dialogs keyboard accessible](https://github.com/kaw393939/is373-ai-chat/issues/19) | [REQ-QUALITY](baseline.md#req-quality) | See issue for access needs |
| P2 | [#20 · Make older conversations and accounts reachable with bounded pagination](https://github.com/kaw393939/is373-ai-chat/issues/20) | [REQ-CHAT](baseline.md#req-chat) | See issue for access needs |
| P2 | [#21 · Specify retention and deliver an owned-data export path](https://github.com/kaw393939/is373-ai-chat/issues/21) | [REQ-PRIVACY](baseline.md#req-privacy) | See issue for access needs |
| P2 | [#22 · Keep dependencies, actions and vulnerability evidence current](https://github.com/kaw393939/is373-ai-chat/issues/22) | [REQ-DELIVERY](baseline.md#req-delivery) | See issue for access needs |
| P2 | [#23 · Audit teaching claims and assess T-shaped engineering outcomes](https://github.com/kaw393939/is373-ai-chat/issues/23) | [REQ-LEARNING](baseline.md#req-learning) | See issue for access needs |

## Suggested first slice

Resolve the time-critical credential dependency and real email access first. In parallel with owner-controlled setup, begin the disposable-test guard, provider terminal-event regression and deployment setup recovery. Then address UI/session races before extracting frontend modules. Each item has its own acceptance and validation; none is closed merely because it appears in this index.

## Baseline and teaching scope

Existing released behavior is recorded in [implementation evidence](../implementation-evidence.md), not recreated as falsely completed issues. Refactoring suggestions remain proposals until tests demonstrate behavior. Advanced attachments/RAG/tools/voice/billing remain discovery scope in the [baseline](baseline.md#scope-boundaries).

This planning setup is tracked by [#1](https://github.com/kaw393939/is373-ai-chat/issues/1). Its completion establishes the backlog, not completion of the application work above.
