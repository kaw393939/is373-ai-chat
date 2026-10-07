# 10 · Make failures understandable

A backup command exits successfully. Has the system become recoverable? Only if the right records, schema, application version and private configuration can be restored within the required time. Recovery is an engineering promise with evidence, not a file existing on disk.

**Learning outcomes:** distinguish backup from restore proof and local survival from disaster recovery; define recovery point/time objectives; reason about schema compatibility; diagnose an interrupted release without destructive guessing. Read [data](03-data.md), [limits](06-operations.md) and [delivery](08-delivery.md).

## What automation inherited

Manual operators could retain an older application directory and copy data to another disk. Automation makes the steps repeatable but does not resolve the compatibility question: can that older program interpret the current data? Humble and Farley's delivery work includes deployment and configuration in the system's lifecycle. A container digest helps identify a candidate; it cannot make a changed schema backward compatible. [Delivery context](references.md#ref-delivery).

PostgreSQL documents logical dumps and other backup approaches as distinct techniques. We use custom-format `pg_dump` archives and `pg_restore`; we do not claim this supplies point-in-time recovery or removes the need to retain secrets and off-host copies. [PostgreSQL backup guidance](references.md#ref-backup).

## Worked case: an image rollback after migration

Consider a hypothetical release changing a column in a way an old image cannot read. Starting the old image may recover a process while leaving user requests broken. The deployment wrapper therefore compares schema revisions before automatic previous-image recovery. If the revision changed, it fails visibly and retains a dump for an operator decision; it does not automatically downgrade data.

Compatible additive changes offer more options, but they still require verification. A migration's `downgrade` function is not proof that lost data can be reconstructed. An operator might forward-fix, use an explicitly compatible old image, or restore a compatible database into a separate target. Each choice trades recovery time against data loss and must follow the actual failure.

Daily/pre-deployment dumps currently live in a protected host directory. They survive app container replacement, not droplet loss. Off-host encrypted retention and restore proof remain [#4](https://github.com/kaw393939/is373-ai-chat/issues/4). A prior local restore checked schema `0001`; it must not be presented as independent restore proof for current schema `0002` or a complete disaster rehearsal.

## Read the recovery boundary

| File/symbol | Decision |
|---|---|
| [Deployment wrapper](../deploy/chat-deploy) | What is saved before migration, and what is inside/outside recovery handling? |
| [Backup script](../deploy/backup.sh) | Which database, permissions and retention does it actually manage? |
| [`Generation`, `generate`](../app/models.py), [services](../app/services.py) | How does interruption differ from completed output? |
| [Implementation evidence](../docs/implementation-evidence.md) | Which restore/restart exercises ran, with which schema? |

An incident explanation should connect a symptom, timestamp, observed release identity, hypothesis and discriminating check. Preserve useful logs without collecting credentials or private prompts. A database-ready health response narrows the diagnosis but does not prove a provider credential works.

## Plan before breaking anything

A recovery point objective (RPO) defines tolerated data loss; a recovery time objective (RTO) defines tolerated restoration delay. Neither is established merely by a daily schedule. Select them with the owner, identify the image/schema/Compose/secret inventory, and rehearse in an empty disposable target. Keep the source database and running service available until the target is verified.

The app-side `PROVIDER_EXPIRES_AT` lease refuses new real-provider requests after its configured time. It does not revoke a key at the provider. Replacing credentials is an operator process and requires a container restart, not an image rebuild. Use synthetic failures for learner exercises.

**Laboratory:** [Lab 10 — resources and recovery](labs/10-resource-recovery.md), including a disposable restore. **Evaluate:** define the checks that would demonstrate restored ownership, conversation records, constraints and schema identity; explain what remains unknown about host-loss recovery. Setup-failure recovery remains [#13](https://github.com/kaw393939/is373-ai-chat/issues/13), and crash/termination behavior needs [#8](https://github.com/kaw393939/is373-ai-chat/issues/8).
