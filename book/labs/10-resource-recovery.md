# Lab 10: demonstrate a bounded restoration, then name its limits

## Problem, objectives and preparation

An operator has a backup file but has never restored it. Prove that expected records and the compatible schema survive restoration, while distinguishing a container cap from reserved host capacity. Bloom emphasis: **apply, analyze, evaluate**.

Complete [preflight](README.md), [operations](../06-operations.md), [recovery](../10-recovery.md) and Lab 03. Know a database dump and the difference between host/container failure. Use an operator-owned local Docker daemon. The fixture creates a new labeled PostgreSQL container with a loopback random port, 256-MiB memory/0.50-CPU/128-PID ceilings; no application data or cloud account is involved. Requirement: [REQ-OPERATIONS](../../docs/project/baseline.md#req-operations).

## Guided recovery rehearsal

Read `recovery` and its `postgres` context in [fixtures.py](fixtures.py), especially container ownership and cleanup. Predict users in original versus restored database after the deliberate data loss.

```sh
uv run python book/labs/fixtures.py recovery
```

Expected checkpoints:

```text
Verified limits: memory=256MiB pids=128 cpu=0.50
Expected: original users=0; restored users=1; restored schema=0003
```

Actual sampled memory varies. The fixture migrates/seeds one synthetic admin, captures a PostgreSQL custom-format dump, truncates only its new lab database, restores into a separate `restore_test` database and verifies counts against the current migration head (`0003` in this revision). The dump stays in process memory and disappears afterward. This proves a small local restoration, not encrypted off-host storage, large-data timings or disaster recovery.

## Fixed fault and smallest repair

`TRUNCATE users CASCADE` is the fixed data-loss event inside the owned disposable container. The repair restores the compatible dump into a separate target and checks content before considering replacement. A successful `pg_restore` exit without record/schema assertions would be weaker evidence. Never generalize this fault command to a shared database.

For monitoring, read `test_monitoring_collector_data` in [admin tests](../../tests/integration/test_admin.py). Its temporary metrics file permits examining stale/unavailable status without stopping the classroom host's collector. Run:

```sh
env -u TEST_DATABASE_URL -u DATABASE_URL uv run pytest -q tests/integration/test_admin.py::test_monitoring_collector_data
```

## Evidence, transfer and reflection

Submit inspected limits, sampled usage, original/restored counts, schema and the monitoring assertion. Distinguish ceilings, observed consumption and a capacity guarantee. Explain what must be recovered if the app container disappears versus the entire host.

Transfer: design an encrypted off-host rehearsal with a synthetic dataset, retention/access policy, measured recovery time and record-level checks. Compare snapshots and logical dumps against stated recovery point/time objectives. Do not provision a paid destination as part of this lab.

## Troubleshooting, cleanup and status

If PostgreSQL readiness fails, inspect only the fixture container's logs. If restore fails, keep the first error; do not retry with production dumps or secrets. The context cleans its exact labeled container and anonymous volumes. The Docker recovery wrapper passed on Linux amd64 in [book CI run 37550661540](https://github.com/kaw393939/is373-ai-chat/actions/runs/37550661540): original users=0, restored users=1 and schema=0002, with the asserted container ceilings. This workstation lacks Docker. This new local restore fixture does not establish off-host restoration. Human pilot remains pending.
