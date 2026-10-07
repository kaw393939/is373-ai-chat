# Lab 07: race a shared invariant and challenge a coverage number

## Problem, objectives and preparation

Two workers see one available generation slot. Can both reserve it? Explain why transaction/lock semantics matter, and why 100% coverage does not answer that question. Bloom emphasis: **apply, analyze, evaluate**.

Complete [preflight](README.md), [data](../03-data.md), [limits](../06-operations.md), [testing](../07-testing.md) and Lab 04. Know async tasks and transactions. The first activity is dependency-only; the concurrency activity needs an operator-owned **local Docker daemon** and enough memory for a capped 256-MiB PostgreSQL container. No app server or real provider is needed. Requirements: [REQ-QUALITY](../../docs/project/baseline.md#req-quality), [REQ-OPERATIONS](../../docs/project/baseline.md#req-operations).

## Guided experiments

```sh
uv run python book/labs/fixtures.py coverage
env -u TEST_DATABASE_URL -u DATABASE_URL uv run pytest -q tests/integration/test_chat.py::test_budget_and_model_enforcement
uv run python book/labs/fixtures.py admission
```

Expected: the mutant obtains 100% measured coverage yet fails the negative ownership example; the budget test passes; the PostgreSQL admission test passes **without skipping**. The admission wrapper creates a new labeled database container on a random loopback port, sets `lab_test` plus its explicit reset marker, and removes only that container afterward.

Read `prepare_run` and `test_parallel_admission_is_atomic`. Explain why each concurrent task has a separate session but shares one database invariant. The test expects one admitted run ID and one 429. A sequential test could pass even if both concurrent requests were incorrectly admitted. SQLite's selected concurrency test skips because it cannot establish PostgreSQL row-lock behavior.

## Fixed faults and repairs

The coverage mutant “allows everyone,” while a positive-only test covers every executable line. The smallest test repair adds a denied cross-account example. The race is a second fixed stress input: two simultaneous requests compete for one slot. The application's row lock and atomic transaction are the current defense. Do not remove locks on a shared environment to demonstrate their value.

## Evidence, transfer and reflection

Submit the mutant output, budget result, genuine PostgreSQL non-skip result and a two-task timeline showing the lock/commit boundary. Explain what the admission test does not prove: sustained load, fairness, process termination, every budget combination or provider billing accuracy.

Transfer: define a daily request limit of one across two different conversations. Write the expected concurrent outcomes and identify the shared row that must serialize them. Compare PostgreSQL-backed admission with an external queue or Redis counter: include transaction coupling, failure recovery and operating cost. Explain whether reservations should be refunded after partial provider work.

## Troubleshooting, cleanup and status

Docker unavailability is a missing prerequisite; keep the activity incomplete rather than presenting a SQLite skip as a pass. A target rejection must be resolved by the owned fixture, not with a public database URL. The wrapper cleans its own container; see preflight cleanup for hard-kill recovery. The coverage fixture was executed during this review. The standalone Docker admission wrapper is authored and statically reviewed but not executed on this workstation, which lacks Docker; existing CI PostgreSQL evidence is a separate record. Human pilot remains pending.
