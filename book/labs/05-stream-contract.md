# Lab 05: a stream needs a defined ending

## Problem, objectives and preparation

Text arrives, then the provider connection ends early. Should the application call that success? Separate byte decoding, SSE framing and provider/domain completion. Bloom emphasis: **apply, analyze, evaluate**.

Complete [preflight](README.md), read [streaming](../05-streaming.md) and [behavioral substitution](../13-engineering-ideas.md). Know generators, JSON and HTTP. HTTPX `MockTransport` supplies every provider byte; no request leaves the process and no real key is used. Requirements: [REQ-CHAT](../../docs/project/baseline.md#req-chat), [REQ-ARCHITECTURE](../../docs/project/baseline.md#req-architecture).

## Guided checkpoints

Read `stream` in [fixtures.py](fixtures.py), the real [adapter](../../app/providers.py) and the frontend `consume` reader in [api.ts](../../frontend/src/api.ts). Predict what differs between a full response and a delta followed by EOF.

```sh
uv run python book/labs/fixtures.py stream
env -u TEST_DATABASE_URL -u DATABASE_URL uv run pytest -q tests/unit/test_providers.py tests/integration/test_chat.py::test_cancel_and_provider_failure_preserve_state
```

Expected fixture output:

```text
Observed gap: premature EOF produces text without a terminal usage event
Expected: decoding each network chunk independently fails
Expected: incremental decoder retains the complete Unicode frame
```

The selected tests pass for explicit provider failures and normalization. They do not prove a terminal-event contract for unexplained EOF. The fixture deliberately splits the UTF-8 `é` between bytes: decoding each chunk independently fails; the incremental decoder succeeds. This Python decoder demonstration illustrates the byte boundary; it does not execute the TypeScript reader.

## Fixed faults and repair boundary

There are two fixed failures. A fragmented character needs decoder state across reads. An incomplete provider response needs an explicit success/failure contract; receiving some text is insufficient. The current EOF gap is tracked in #12/#18. Do not write a reassuring success assertion to hide it or claim the application was repaired by running this fixture.

## Evidence, transfer and reflection

Submit the two event lists, decoded text and a contract table for success, explicit failure, cancellation, timeout and unexplained EOF. State whether partial text and reservations survive each case. Separate transport closure from the generation's durable terminal state.

Transfer: in a private branch, propose a provider-neutral terminal event and one shared contract test applicable to mock, Responses and compatible adapters. Explain what cannot be standardized across vendors. Compare treating unexplained EOF as failure with using a validated vendor completion signal; document the compatibility cost. The capstone can implement this policy using fake transport only.

## Troubleshooting, cleanup and status

If a real network error appears, stop: the documented fixture patches the adapter's HTTPX client and should make no external request. Missing output indicates a fixture/runtime error, not evidence about a provider account. Temporary fixtures require no teardown. Both contained fault demonstrations were maintainer-executed on October 6, 2026; reader success and a completed app-wide terminal contract remain pending.
