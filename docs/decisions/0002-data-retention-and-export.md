# ADR 0002: Retention, owned-data export and deletion scope

Status: implementation policy for this teaching application; October 7, 2026. Requirement: [REQ-PRIVACY](../project/baseline.md#req-privacy). Delivery and acceptance criteria: [#21](https://github.com/kaw393939/is373-ai-chat/issues/21).

## Decision and current limits

Keep accounts and chat history for the operator's ongoing service. An owner can delete a conversation, which cascades to its messages and generation records. [Account erasure #27](https://github.com/kaw393939/is373-ai-chat/issues/27) is a separate follow-up; disabling an account prevents access but does not erase its records. There is no automatic age-based deletion of chats, accounts, daily usage or audit events. Do not describe those records as having a finite retention period until an implemented cleanup policy exists.

Provide an authenticated export containing only the caller's profile, conversations, messages and generation outcomes. `GET /api/account/export?section=conversations|messages|runs` returns at most 100 items with an owner-bound cursor and format `firehose360-owned-v1`. Walk each section to collect the complete export. Pages are not one atomic snapshot; an account changing during export can produce a mixed-time view. Exclude password hashes, sessions, refresh/recovery tokens, factor secrets, recovery codes, outbox payloads and other users' information. This is an application portability feature, not a legal compliance certification. Tests exercise ownership with multiple users and verify the exclusions.

| Data | Retention and disposal |
|---|---|
| Conversation content and generation metadata | Stored until the owner deletes its conversation; included in owned export |
| Account profile and daily usage | Kept while the service uses the account; account erasure is a tracked follow-up |
| Administrative audit events | Kept for operational review; no automatic age limit currently |
| Refresh/recovery/throttle metadata | Expiry prevents use; daily `app.cli prune` deletes expired records and related session tokens |
| Transactional email payload | Encrypted while pending; cleared on accepted delivery, expiry or bounded retry failure |
| Terminal outbox metadata | Daily prune deletes non-pending records older than 32 days; provider retention is independent |
| Encrypted daily backup | 14-day server retention; 28-day recovery-computer retention, pruned only after a successful checked pull |
| Older deployment snapshots | Protected local dumps may predate encryption; explicitly inventory/retire them after verified recovery |

Backup contents capture the database and protected configuration at a point in time. A conversation deleted today can remain in an older encrypted backup until that backup expires. A restore must reconcile subsequent deletions and revoke restored sessions/recovery links before reopening the service. A successful restore does not prove that live authorization remains appropriate. Keep the decryption identity on the recovery computer; the application host receives only an encryption recipient.

## Notice to users

Prompts and selected conversation history are sent to the configured LLM provider to generate an answer. Transactional addresses and message contents are sent to the configured email provider. Their processing/retention rules are outside this application's deletion controls. The operator selects providers, credentials and service policies; the public teaching host is unsuitable for secrets or regulated information. The frontend should link this policy and the security-reporting channel.

## Why this scope

An export makes ownership boundaries observable without silently deleting data or inventing a retention guarantee. Export and deletion solve different problems: deletion needs durable revocation, pending-mail handling, auditing rules and recovery behavior. Keep those acceptance criteria in the deletion issue rather than creating several conflicting policy documents. The operator must choose any stricter account/audit retention before enabling it.
