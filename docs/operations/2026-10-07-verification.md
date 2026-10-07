# Existing-host operations verification

Observed October 7, 2026 UTC (October 6 Eastern). Acceptance remains in [#4](https://github.com/kaw393939/is373-ai-chat/issues/4), [#5](https://github.com/kaw393939/is373-ai-chat/issues/5) and [#24](https://github.com/kaw393939/is373-ai-chat/issues/24); this dated record preserves evidence rather than duplicating their checklists.

## Encrypted copy and measured restoration

The owner selected existing storage/host access with no new paid resources. [Backup implementation](../../deploy/backup.sh) and the [vault tool](../../scripts/backup-vault.py) were installed on the existing Ubuntu host and owner's FileVault-enabled Mac. The private age identity stays on the recovery computer; the host holds its public recipient. A distinct restricted SSH export key permits recognized ciphertext retrieval and checksum receipts. Strict host-key verification uses the already authenticated server identity. Private directories/keys/configuration were checked at 0700/0600; no decryption identity or runtime credential was committed.

`chat-backup.timer` is enabled/active and scheduled daily at 07:00 UTC. The Mac's `com.firehose360.backup-vault` LaunchAgent pulls hourly while awake/connected; its first scheduled run exited 0. The first archive, `daily-20261007T003419Z.tar.age`, reached the off-host vault. Ciphertext size/hash, authenticated age decryption, safe archive paths and manifest hashes passed verification. Server retention is 14 days and vault retention 28 days. An hourly receipt is distinct from the archive's creation time. The collector timer is active, its latest service result is success, and sanitized dashboard input reported both local and off-host backups fresh.

[Machine-readable evidence](../audit/2026-10-07-off-host-restore.json) records restoration into an empty isolated PostgreSQL database. It restored schema `0002`, two users including one administrator, one conversation, two messages and one generation. Whole-row comparisons matched source account/role/ownership, conversation content, generation and outbox records; only comparison results are retained here. The exact historical image recorded in that evidence successfully read restored data through its SQLAlchemy models with mock provider/disabled mail.

Database creation, `pg_restore` and count checks took **1.745 seconds** for this small dataset. That interval excludes backup download/decryption, OS/proxy/configuration/service restoration and operator response. The dump was created at 00:34:19 UTC; the measured restore finished at 00:46:49 UTC, a 12-minute-30-second snapshot age. A real incident could lose writes after the dump. Daily scheduling and these timings establish neither a guaranteed recovery point nor a complete host-loss recovery time.

The source outbox was empty; this record does not establish nonempty pending-mail restoration. The new schema-`0003` candidate requires its own release-compatible rehearsal. A second protected identity copy, an agreed actionable failure-alert channel, cloud-account controls and an independent fresh-host/reader exercise are still unverified. The existing Mac is an economical off-host destination with availability limits; it is not always-on storage.

## Scoped release access

Reviewed root-owned deployment/SSH/release-policy wrappers were installed. Development, QA and production have distinct forced-command keys, private configuration and GitHub environments restricted to main. A dev key's arbitrary shell command and a QA key's attempted dev command were both refused. Existing personal operator access was preserved; `visudo` validated the narrow deploy/export entries.

Production requires the owner reviewer, disables administrator bypass and permits self-review in this sole-owner repository. This is authenticated approval, not independent two-person control. Immutable GitHub releases are enabled for subsequent releases. QA has an approved ordinary synthetic smoke account, separate from administrator access and production data. Credentials were passed privately to its environment secrets.

Installing this configuration is separate from executing the new pipeline. Link the successful candidate's image/process/browser/scan results and accepted dev/QA digest before selecting production. Record the production approval, deployment and immutable release separately in [delivery evidence](../implementation-evidence.md).
