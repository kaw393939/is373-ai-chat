# Implementation evidence

Updated October 7, 2026 UTC (October 6 Eastern). GitHub issues own acceptance criteria and current status; this page links executed evidence and its limits.

## Current application release

[Immutable application 2.0.0](https://github.com/kaw393939/is373-ai-chat/releases/tag/v2.0.0) is deployed at [production](https://firehose360.com), [development](https://dev.firehose360.com) and [QA](https://qa.firehose360.com). All three use the same tested artifact:

- Source: `ea95a452e3884afb7b729bd27444f89cb95e7271`
- Image: `ghcr.io/kaw393939/is373-ai-chat@sha256:1d05c83616e855e6172d85000e058c1c5383b112eff26f806c416fc687933221`
- Version/schema: `2.0.0` / `0003`
- [Delivery and QA acceptance](https://github.com/kaw393939/is373-ai-chat/actions/runs/37556269023), followed by [production promotion](https://github.com/kaw393939/is373-ai-chat/actions/runs/37557347918), both passed. Production reused the accepted digest without rebuilding.

The [dated delivery record](audit/2026-10-07-delivery.md) and [sanitized data](audit/2026-10-07-delivery.json) retain identities, actual results and downloaded release-asset hashes. Production required the owner reviewer; the assistant exercised delegated approval under standing deployment authorization. It was not an independent human review. Main-only environments, distinct forced-command keys and disabled administrator bypass remained enforced.

## Tests, security and failure behavior

The candidate passed **164 PostgreSQL application tests, 12 Node tests, 11 exact-image browser journeys and 99 delivery/operations/safety tests**. Python application coverage measured 1,289 lines and 278 branches at 100% under the configured exclusions. This metric does not cover React or host scripts. CLI/parser, disconnect and lifecycle paths have documented exclusions with separate execution evidence; percentage coverage is not proof of complete behavior.

Formatting, types/build, lint, migration parity, locked dependency audit, SBOM and the unchanged image vulnerability gate passed. Zero fixable HIGH/CRITICAL findings remain in the scanned image; **44 unfixed HIGH package/CVE pairs across eight IDs** remain disclosed in the immutable release report. [Exact security pins](audit/2026-10-06-image-security-pins.md) record the vendor fixes that unblocked the candidate. Hardening reduces exposure without making these remaining advisories harmless.

The exact-image, two-process experiment covered shared global/user/conversation/replay admission and termination. SIGTERM saved 58 partial characters, marked cancellation and released the reservation before exiting in 10.788 seconds. Abrupt KILL saved the prompt/reservation but lost partial output; capacity was reclaimed 0.561 seconds after the actual 149.999-second lease expired. Synthetic mail acceptance followed by KILL/restart produced two attempts, one accepted delivery, sent state and erased encrypted payload. This is controlled provider evidence, not production inbox delivery.

Regression evidence includes provider EOF/terminal semantics, stale UI ownership, cross-tab refresh/logout, duplicate-registration and administrator-update races, recent-authority fences, quota/email privacy, MFA/recovery, typed boundaries, bounded pagination and owner-scoped export. [Query-plan measurements](audit/2026-10-06-pagination-plans.md) disclose finite fixture sizes and actual scans/sorts rather than claiming constant-time keyset queries. [Registration race evidence](audit/2026-10-06-registration-race.md) records real database uniqueness enforcement.

## Browser and operations checks

Native Chrome verified ordinary QA login, mock streaming, saved history after reload and logout. Production checks verified existing administrator login, one short real OpenAI response, the saved response after reload, loaded accounts/budgets, live CPU/memory/disk/container limits, local/off-host backup freshness, account controls and logout. Seven footer links expose the textbook, downloadable edition, source, issues, security reporting, licenses and privacy decision. Password changes and administrator factor enrollment were not performed during this check.

[Existing-host operations evidence](operations/2026-10-07-verification.md) records encrypted off-host copies to the owner's FileVault-enabled Mac, scheduling and scoped access. The [current schema-0003 rehearsal](audit/2026-10-07-current-release-restore.json) passed complete-row/schema comparison and matching-image SQLAlchemy reads; its measured database phase and empty-outbox limits are explicit. [Backups](operations/backups.md) owns the recovery procedure. [Real staging rejection](audit/2026-10-07-staging-rejection.json) left active release sentinels unchanged before any migration or restart. Controlled later-failure tests complement that bounded host rehearsal.

## Teaching edition

[Immutable book 0.3.0](https://github.com/kaw393939/is373-ai-chat/releases/tag/book-v0.3.0) contains the exact checked HTML from source `d9439dd4ccadad706d34ec8de5c2f205baec2d05`, with source/build identity and a ZIP checksum. Its independent [book verification](https://github.com/kaw393939/is373-ai-chat/actions/runs/37555797453) passed strict source/link checks, all eight executable fixture modes and browser/mobile checks across 41 generated pages. Application and book versions are separate. The release does not establish independent fresh-reader or classroom validation; [#23](https://github.com/kaw393939/is373-ai-chat/issues/23) and [#26](https://github.com/kaw393939/is373-ai-chat/issues/26) retain those gates.

## Remaining work and limits

Production email is disabled pending actual sender DNS/API setup and verification/recovery/reply receipt. The existing Google mailbox remains the receiving destination. Administrator MFA implementation is deployed, but the owner must enroll, protect recovery codes and enable required-admin enforcement. Cloud-account firewall/alert settings, delivered failure alerts, a second protected backup identity copy, independent fresh-host installation and human assistive-technology checks remain open. Export does not implement account erasure; [#27](https://github.com/kaw393939/is373-ai-chat/issues/27) tracks that separate scope.

The owner chose to retain the temporary provider key until its application lease ends **October 7, 2026 at 19:58:49 UTC / 3:58:49 PM Eastern**. The application deadline stops new paid generations; it does not revoke the key at the provider. Replacement and provider-side revocation remain [#2](https://github.com/kaw393939/is373-ai-chat/issues/2).

This remains a single shared amd64 host with bounded resources and short release interruptions. Text streaming, conservative reservation units and an intermittently connected Mac vault have explicit limits. These checks do not prove high availability, sustained-load capacity, every provider's compatibility or full host-loss recovery.

## Historical deployment records

The initial deployment and browser/provider checks are preserved in [run 37523682890](https://github.com/kaw393939/is373-ai-chat/actions/runs/37523682890), followed by the [first review delivery](https://github.com/kaw393939/is373-ai-chat/actions/runs/37529676892) and [schema-0002 edition delivery](https://github.com/kaw393939/is373-ai-chat/actions/runs/37550580435). Their smaller test counts and restore datasets describe those revisions, not today's candidate. The earlier public schema-0002 image was `sha256:1d2a4fa2671d9e0f57ad1f314d03d7aaa15ebdde17df283d5aee4d45a5b66a0b`; its [off-host restore record](audit/2026-10-07-off-host-restore.json) remains historical evidence.
