# Current-release off-host restoration

Observed October 26, 2026 Eastern; the successful local rehearsal completed
October 27 at 00:55:31 UTC. This is AI/operator evidence for
[REQ-OPERATIONS](../project/baseline.md#req-operations),
[recovery issue #4](https://github.com/kaw393939/is373-ai-chat/issues/4) and the
preparation for [HOST-002](https://github.com/kaw393939/373_hosting/issues/5).
It is not an independent reader's recovery or a complete host rebuild.
Refs #4; its remaining acceptance criteria stay open.

## Recovery point and integrity

The existing off-host vault held `daily-20261026T070006Z.tar.age`, a 41,160-byte
encrypted archive created at **2026-10-26 07:00:06.093797 UTC**. Its ciphertext
matched the existing receipt, authenticated age decryption succeeded, and every
file checksum in the manifest matched. Archive validation accepted only expected
regular files with bounded member count, individual size and total size. Synthetic
negative cases rejected absolute paths, traversal, symlinks, hardlinks, device
files, unexpected files, duplicate members and oversized members. No identity,
configuration values, database rows or database fingerprints were published.

The manifest identified schema `0003` and the recorded release image
`ghcr.io/kaw393939/is373-ai-chat@sha256:1d05c83616e855e6172d85000e058c1c5383b112eff26f806c416fc687933221`.
The recovery identity stayed on the recovery computer. The harness verified
protected configuration bytes in memory without loading that configuration into
the restored application or extracting separate configuration files.

## Actual isolated restoration

[Sanitized machine-readable evidence](../audit/2026-10-26-current-release-restore.json)
records a new local PostgreSQL 17 target with no network connectivity, published
ports or host bind mounts. Its root filesystem was read-only, its database used
ephemeral tmpfs, and limits were 384 MiB memory, 0.5 CPU and 128 PIDs. Only that
new database received `pg_restore`, using `--exit-on-error --single-transaction
--no-owner --no-privileges`. The live database was neither queried nor restored
or written by this rehearsal.

Restoration completed; Alembic revision matched `0003`, the expected fourteen
application tables were present, and all restored constraints were validated.
Read-only queries recorded aggregates without emitting row contents.

The initial public GHCR pull was unauthorized. Under the owner's existing
authorization, the operator verified the selected existing server image and
exported it with Docker save. The export was age-encrypted, transferred off-host
and authenticated-decrypted into local Docker load. No registry authentication
was changed. The local image's revision/version labels matched the recorded
`v2.0.0` release at commit
`ea95a452e3884afb7b729bd27444f89cb95e7271`.

That image then read every mapped row across all fourteen application models in
a read-only SQLAlchemy transaction. Its counts matched the restored database's
counts. The reader shared the isolated PostgreSQL network namespace, had no
egress, and used bounded resources, a read-only filesystem and dropped
capabilities. Its normal application server was not started; mail was disabled,
the provider was mock, and no backed-up `.env` was loaded. Version and commit
reported by the image also matched the recorded release.

## Measurements and failed attempt

| Measurement | Actual scope and result |
|---|---|
| Database creation/readiness, restore and schema/aggregate checks | **1.929 seconds** |
| `pg_restore` alone | **0.054 seconds** |
| Database checks completed | **2026-10-27 00:54:13.849773 UTC** |
| Backup age at those checks | **64,447.756 seconds**, about **17.90 hours** |
| Complete local harness run | **79.469 seconds**, including image wait, application read and cleanup |

These timings describe this small snapshot and local machine. The database
interval excludes archive download/decryption, image availability, application
reading, operator response and complete service/host recovery. The backup age is
the observed recovery point, not a guaranteed maximum data-loss window.

The first local harness attempt accepted a Unix-socket readiness check and failed
at `pg_restore`. PostgreSQL's image uses a temporary Unix-socket-only server
during initialization; the harness was corrected to require the final TCP
listener. A fresh target then passed. Detailed stderr from the initial failure
was intentionally not retained, so this record does not claim a more specific
failure diagnosis. Both that failed target and the successful rehearsal's two
containers were removed. All newly created plaintext scratch was removed;
encrypted vault archives were retained. Existing local containers were untouched.

## What remains unverified

The manifest has file hashes, schema/image identity and creation time, **not row
counts or row fingerprints**. No live-source comparison was performed; the two
count checks read the same restored snapshot. This result does not claim
live-source row parity or recovery of writes newer than the backup.

The snapshot's outbox and factor tables were empty. Nonempty pending-mail
reconciliation, factor-secret decryption, restored-user authentication, database
roles/ownership/ACLs, actual provider/mail delivery and full host/OS/proxy/DNS/TLS
recovery were not exercised. Workspace and other applications have separate
recovery inputs. A second protected identity copy and delivered failure alerts
remain independent acceptance work in
[#4](https://github.com/kaw393939/is373-ai-chat/issues/4) and
[#5](https://github.com/kaw393939/is373-ai-chat/issues/5); clean-host installation
remains in [#7](https://github.com/kaw393939/is373-ai-chat/issues/7).

The [backup runbook](backups.md), [backup implementation](../../deploy/backup.sh),
[vault tool](../../scripts/backup-vault.py) and
[release models](https://github.com/kaw393939/is373-ai-chat/blob/ea95a452e3884afb7b729bd27444f89cb95e7271/app/models.py)
explain the mechanism. The [October 7 record](2026-10-07-verification.md) remains
historical evidence with its separately stated scope and measurements.
