# Lab 04: prove ownership and role boundaries

## Problem, objectives and preparation

A user knows another conversation's identifier. Does a valid login permit reading, editing or streaming into it? Demonstrate identity, ownership and administration as separate decisions. Bloom emphasis: **understand, apply, analyze**.

Complete [Lab 01](01-token-boundaries.md), [Lab 02](02-request-trace.md), [preflight](README.md) and [identity](../04-auth.md). Know 401/403/404 and assertions. All accounts below are synthetic in temporary databases; no public registration is performed. Requirement: [REQ-IDENTITY](../../docs/project/baseline.md#req-identity).

## Guided investigation

Before running, predict a matrix for unauthenticated caller, owner, other ordinary user and administrator. Include GET/PATCH/DELETE conversation, POST stream and GET admin overview. Does an administrator automatically own every conversation?

```sh
env -u TEST_DATABASE_URL -u DATABASE_URL uv run pytest -q tests/integration/test_chat.py::test_owned_chat_stream_history_rename_delete tests/integration/test_web_security.py::test_cross_account_writes_and_admin_methods_are_denied
```

Expected: both tests pass. Inspect [chat assertions](../../tests/integration/test_chat.py) for cross-account GET/DELETE/cancel and [security assertions](../../tests/integration/test_web_security.py) for PATCH/stream/admin denial. Trace each case to `current`, `admin` or `owned`. Do not infer that the tests cover every endpoint simply because these examples pass.

Run the contained teaching mutant:

```sh
uv run python book/labs/fixtures.py coverage
```

Expected: a synthetic policy returning `True` obtains 100% measured coverage from a positive example; a negative ownership assertion detects its defect. That module exists only in a temporary directory and is not the application's policy.

## Fixed fault and repair

The other account's requests are intentional forbidden inputs. The ownership query—not hiding buttons—is the existing app defense. The synthetic mutant supplies a second fault: positive-only tests cannot distinguish a correct ownership predicate from “allow everyone.” The smallest useful repair is an ownership predicate **and** a negative behavioral assertion, not additional calls that merely increase coverage.

## Evidence, transfer and reflection

Submit the predicted/corrected matrix, exact server functions, passing selected tests and the mutant counterexample. Explain 404 concealment versus 403 role denial as this app's policy, not a universal HTTP rule. Explain why an admin interface is not a security boundary by itself.

Transfer: propose collaborator access to one conversation. Define owner, reader and editor permissions; name the schema/policy/tests that would change. Compare explicit membership with an admin-only override and justify least privilege. Keep this as a design or private local change until its acceptance tests are defined.

## Troubleshooting, cleanup and status

An unexpected 401 may be a session setup problem; distinguish it from an ownership denial by reading the fixture's login sequence. Use the exact temporary-test command instead of supplying server credentials. Tests and synthetic mutant create no persistent service. Existing app assertions and the mutant are maintainer-checkable; human learner assessment remains pending.
