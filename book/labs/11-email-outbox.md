# Lab 11: prove a delivery boundary without sending mail

## Problem, objectives and preparation

The database commits a recovery request; the sender is temporarily unavailable. Explain how a bounded outbox preserves intent, avoids changing idempotency identity and erases sensitive payloads when finished. Bloom emphasis: **apply, analyze, evaluate**.

Complete [preflight](README.md), [email](../11-email.md), [data](../03-data.md) and Lab 04. Know transaction commit, retries and a bearer secret. Tests create synthetic encrypted messages and use mock/fake HTTPS transport. No Resend account, real address, inbox, DNS change or provider key is needed. Requirement: [REQ-EMAIL](../../docs/project/baseline.md#req-email).

## Guided checks

Read `token_email`, `enqueue` and `drain` in [email.py](../../app/email.py). Predict what is committed before network delivery, what is stored hashed versus encrypted, and what happens after six failures.

```sh
env -u TEST_DATABASE_URL -u DATABASE_URL uv run pytest -q tests/integration/test_email.py::test_retry_is_bounded_and_erases_payload tests/integration/test_email.py::test_registration_verification_approval_and_email_recovery
```

Expected: both tests pass. Inspect the first test's `Unavailable` fake: six attempts retain one provider idempotency key, final status becomes `failed`, payload is erased, and another drain does not retry it. The second test verifies address control separately from approval, single-use/wrong-purpose link rejection, generic recovery response, revocation and mocked delivery cleanup.

## Fixed fault and smallest repair

The fake sender raises an availability error for every attempt. The app records bounded retry state instead of assuming that a database commit means inbox receipt. Stable idempotency identity matters when a real sender accepted a request but its acknowledgement was lost. These tests model failure and contract behavior; they do not independently prove Resend's behavior after an actual lost acknowledgement.

Create a four-state table: pending, sent, failed and expired. Name the payload-retention rule, whether another attempt is permitted and which metadata remains. Explain why changing the encryption key while pending payloads remain is a separate operational risk.

## Evidence, transfer and reflection

Submit passing test output, the state table and a sequence diagram showing commit → worker → provider → acknowledgement. Distinguish **queued**, **provider accepted** and **inbox received**. Explain verification versus administrator approval without using them interchangeably.

Transfer: propose a lost-acknowledgement fake that records the first accepted key then raises, and deduplicates a later same-key retry. Define the assertion proving one effective delivery. Compare provider idempotency with relying on row locks alone. Separately diagram SPF, DKIM, DMARC and MX responsibilities; a unit test cannot validate those live DNS/inbox boundaries.

## Troubleshooting, cleanup and status

A real API authentication or network failure indicates wrong test wiring: the supplied tests use mocks and temporary data. Stop instead of entering a real key. Tests require no worker/server teardown. These are existing maintainer-checkable tests; real sending activation and human learner assessment remain independent pending work.
