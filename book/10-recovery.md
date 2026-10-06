# 10 · Make failures understandable

Daily and pre-deployment PostgreSQL dumps are stored outside containers under a protected host directory. Local dumps survive container replacement but not droplet loss. Add an encrypted off-host destination and test restoration before relying on disaster recovery. DigitalOcean snapshots complement, rather than prove, database recovery.

Restore into a separate empty database first:

```sh
# The dump and target database must be appropriate for this release.
docker compose exec -T db createdb -U chat restore_check
docker compose exec -T db pg_restore -U chat -d restore_check < backups/SELECTED.dump
```

Inspect restored users, conversations and schema revision. Do not overwrite production merely to test the command. Keep database, application image, compatible Compose configuration and required private secrets together in a recovery inventory.

A deploy failure before migration leaves the old app available where possible. After a schema change, selecting an old image may be incompatible. Deployment therefore checks schema identity before automatic app rollback; recovery after changed schema needs a deliberate decision.

Operational exercises:

1. Break a test and demonstrate that main cannot publish through the gate.
2. Cause a provider failure; verify a saved failed run and bounded reservation.
3. Revoke a session; verify immediate rejection of its JWT.
4. Exhaust concurrent/daily limits from two requests and inspect persisted counters.
5. Stop the collector and inspect stale metrics.
6. Restore a dump into a disposable database and verify its records.
7. Compare public release identity with GitHub and the container digest.

A one-day provider key has an application-side lease (`PROVIDER_EXPIRES_AT`); the adapter refuses new requests after it. This does not revoke the key at the provider. The operator must replace/revoke credentials deliberately. Provider changes require a container restart, not an image rebuild.

**Exercise:** write the evidence that would distinguish a working recovery from a script that merely exited successfully.
