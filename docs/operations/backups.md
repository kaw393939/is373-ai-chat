# Encrypted backups on existing infrastructure

Canonical requirement: [REQ-OPERATIONS](../project/baseline.md#req-operations). Acceptance and current status: [#4](https://github.com/kaw393939/is373-ai-chat/issues/4). This runbook uses the existing application host and the owner's recovery computer; it adds no paid storage service. See the [retention decision](../decisions/0002-data-retention-and-export.md) before handling a dump.

## Trust and retention

The server has an **age public recipient**; the recovery computer holds the separate **age identity** needed to decrypt. A restricted SSH export key permits only `list`, `fetch` of recognized encrypted archives and a checksum receipt. It cannot open a shell or download `.env`/plaintext dumps. Pinned SSH host keys protect the transport; SHA-256 detects incomplete/corrupt transfers; age authenticates decrypted contents. Obtain a host pin through an already authenticated connection or independently confirmed fingerprint, never by trusting an unverified `ssh-keyscan` result.

The daily server job packages a PostgreSQL custom-format dump, protected `.env`, Compose configuration, image identity, optional release record and a manifest. It takes the same release lock as the deployer before reading these files or dumping the database, so a migration cannot mix one schema with another release's configuration. It verifies a nonempty dump and captures Alembic revision before encryption. Manifest checksums stream from disk without loading the dump into memory. Restricted scratch files are removed on success/failure; ciphertext is published only after the encryption pipeline succeeds. Existing deployment dumps are not silently purged. Server ciphertext ages out after 14 days. The recovery vault removes recognized ciphertext older than 28 days only after a successful checked pull.

The Mac pulls hourly while awake/connected. This is an economical first off-host copy, with availability limits: a sleeping/offline recovery computer cannot receive backups. Dashboard freshness and the CLI must show that honestly. A recent receipt for an old archive does not make the backup fresh. A 36-hour-old dump is stale. A managed always-online destination is a later infrastructure decision.

## Installation

Install `age` from the vendor-recommended package registry (`brew install age` on macOS, `apt install age` on Ubuntu 24.04). Generate an identity on the recovery computer with `umask 077; age-keygen -o recovery.age`; derive its public recipient with `age-keygen -y recovery.age`. Never copy the identity to the application host or GitHub. Store a second protected recovery copy in the operator's password manager/offline recovery storage. Losing the only identity makes all encrypted archives unrecoverable.

Copy the public recipient to `/etc/chat-backup/recipients.txt` (root-owned, directory 0700/file 0600). Install [backup.sh](../../deploy/backup.sh), [chat-backup-export](../../deploy/chat-backup-export) and [chat-backup-ssh](../../deploy/chat-backup-ssh) at their documented fixed `/usr/local` locations. The sudoers entry permits only the root-owned export program; validate it with `visudo -cf`. Attach the export public key with `restrict,command="/usr/local/lib/chat-backup-ssh"` to the authorized operator account, preserving existing administrative access.

Run the encrypted job once, then fetch with:

```sh
uv run python scripts/backup-vault.py pull \
  --host OPERATOR@HOST --key /private/backup-export \
  --known-hosts /private/known_hosts --destination /private/backups
uv run python scripts/backup-vault.py status --destination /private/backups
```

The vault directory must be 0700 and key 0600. The command exits unsuccessfully for stale/missing/corrupt copies, transfer interruption, an unsafe filename or missing host pin. Scheduler logs contain generic failure messages; detailed evidence stays protected. Enable the existing daily `chat-backup.timer` only after successful first encryption and restore. Schedule the pull on the recovery computer and route failed/stale checks to an agreed operator channel; system logs alone are not an availability alert.

## Restore rehearsal

1. Select a specific archive/receipt and verify its ciphertext hash. Decrypt **on the recovery computer** into a new 0700 scratch directory (`age -d -i /private/recovery.age -o archive.tar BACKUP.tar.age`). Review tar paths before extraction; reject absolute paths, symlinks and traversal. Verify every extracted file against `manifest.json`.
2. Create an isolated PostgreSQL container/database with no public ports. For a content/schema rehearsal, restore the explicit file with `pg_restore --exit-on-error --single-transaction --no-owner --no-privileges --dbname EXPLICIT_TEST_DB database.dump`. These flags exclude owner/ACL recovery; a real service restoration must separately restore and review its database roles/grants. Do not point destructive tests at production; the repository's target guard requires an explicit loopback `*_test` database/reset acknowledgement.
3. Compare schema and aggregate counts against the backup manifest/source snapshot; check sampled ownership/roles, messages, generations and encrypted pending outbox without publishing personal values. Email stays disabled and the provider stays mock. Do not replay live mail or credentials.
4. Before reopening a restored real service, revoke sessions/recovery links, reconcile deletions since the selected backup and review factor/outbox keys. Record elapsed restore time and backup age/data-loss window. A small rehearsal is not a capacity guarantee.
5. Destroy only the isolated rehearsal container/data and remove plaintext scratch. Keep sanitized evidence linked to #4 and the precise release identity.

If a helper validates a file header before passing its descriptor as child stdin, use an unbuffered file or explicitly reset the underlying descriptor. A buffered reader's logical `seek(0)` can leave the descriptor after its read-ahead buffer; a child then misses the header. The [current-release rehearsal](2026-10-07-verification.md#current-schema-0003-restoration) reproduced this harness failure, corrected it and completed a fresh restore. File integrity and successful encryption are necessary checks; restoration proves a different part of recovery.

Implementation references: [age usage](https://github.com/FiloSottile/age#usage), [PostgreSQL backup](https://www.postgresql.org/docs/17/backup-dump.html). The deployment issue owns pre-migration snapshots/recovery; this issue owns encrypted off-host recovery and freshness.
