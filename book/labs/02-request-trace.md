# Lab 02: follow a user promise through one request

## Problem, objectives and preparation

A stakeholder asks, “Where is my conversation saved, and why can another user not see it?” Produce a trace that names the responsible boundary instead of listing frameworks. By the end, distinguish browser/proxy transport from application policy, explain a transaction, and connect an assertion to a user-visible promise. Bloom emphasis: **understand, apply, analyze**.

Complete [preflight](README.md), read [the system](../01-system.md) and [reading code](../00-reading-code.md). Prerequisites: HTTP methods/status codes, Python functions and a basic SELECT. No Docker, browser server or provider account is required. Requirement anchor: [REQ-CHAT](../../docs/project/baseline.md#req-chat).

## Worked path and guided checks

Read `create_conversation`, `stream` and `conversation` in [routes](../../app/main.py), `owned`, `prepare_run` and `generate` in [services](../../app/services.py), then [the request fixture](../../tests/conftest.py). Make a six-row table: input → authentication → ownership → transaction/admission → provider → persisted/output state. Name the function and a failure at each row.

Run:

```sh
env -u TEST_DATABASE_URL -u DATABASE_URL uv run pytest -q tests/integration/test_chat.py::test_owned_chat_stream_history_rename_delete
```

Expected: the selected test passes. Read its assertions: a streamed reply has `started`/`completed` events, history stores two messages, duplicate request keys get 409, another account gets 404, and the owner can delete the conversation. These are ASGI integration checks: HTTPX calls the app in-process. They do **not** traverse DNS, TLS, Traefik or a real browser.

Checkpoint: explain where the transaction ends before waiting for model output. Predict which stored records remain if the provider fails. Consult `generate` to check the prediction.

## Fixed fault and repair

The fixture deliberately tries the first account's conversation after authenticating as a different account. Predict 404 before locating the assertion. The rejected request is the controlled fault; the server's ownership predicate is the existing repair. Draw the counterfactual path if it queried by conversation ID alone. Do not remove the running app's guard.

## Evidence, transfer and reflection

Submit the six-row trace, selected test output, source SHA and one assertion-to-requirement link. Explain why a passing in-process test cannot establish proxy/TLS behavior. For independent transfer, trace `rename` without using the worked route list: identify its schema validation, ownership check, commit and returned status. Name one missing check you would add if rename became a paid operation.

Compare an opaque server session with this app's JWT/session-family checks. Which boundary remains necessary in either design? AI may draft the trace; you must correct it against the exact code and explain one exception path orally.

## Troubleshooting, cleanup and status

A fixture failure can reflect schema/configuration or an actual regression; inspect the first failed assertion rather than guessing from the final HTTP status. The test uses a temporary database when the supplied command is used and needs no service teardown. Keep only your evidence record. This activity links existing tests and is maintainer-checkable; human learner completion and timing remain pending.
