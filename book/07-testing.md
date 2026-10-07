# 7 · Test contracts, not implementation trivia

A passing test can show that an assertion held for a particular setup. It cannot automatically show that the assertion addressed the right user promise. Our task is to select evidence for ownership, accounting and failure behavior, then state its limits.

**Learning outcomes:** distinguish unit, integration and browser evidence; interpret the coverage denominator; explain why PostgreSQL is needed for a row-lock race; design a regression that fails for a meaningful reason. Read [data](03-data.md), [identity](04-auth.md) and [limits](06-operations.md).

## A human practice before a percentage

Kent Beck's *Test Driven Development: By Example*, published in November 2002 with a 2003 copyright edition, develops behavior through small executable examples and refactoring. It teaches a feedback practice rather than a target assertion count. Tests existed before this book, and TDD is not identical to writing tests after implementation. [Publisher's record and author preface](references.md#ref-beck).

AI can generate both a function and a test repeating that function's assumptions. Their agreement is therefore weaker evidence than an independently stated invariant. Compare the intended behavior with a real counterexample before trusting a generated suite.

## Worked case: a guessed conversation ID

Two synthetic accounts have distinct conversations. A test sends account A's valid token while requesting account B's conversation. The correct result follows the ownership contract, not whether a button is hidden. Removing the ownership check should make the test fail. Merely asserting that `owned` was called could survive a broken implementation of `owned` itself.

Different layers establish different facts. Unit tests inspect configuration, password/JWT behavior and provider normalization. Integration tests invoke HTTP authentication, rotation/reuse, policies, CRUD, budgets, cancellation, email and monitoring against a migrated database. The PostgreSQL concurrency test races admission and requires only one request to succeed; SQLite's fast local behavior cannot prove PostgreSQL lock semantics. Python Playwright then follows visible user journeys through the actual compiled UI and image.

## Read the evidence

| File | Contract to inspect |
|---|---|
| [Security tests](../tests/unit/test_security.py) | Which invalid claims fail, and which authority checks occur elsewhere? |
| [Web security tests](../tests/integration/test_web_security.py) | Does a cross-account request fail through the API? |
| [`test_parallel_admission_is_atomic`](../tests/integration/test_chat.py) | Why must this case use PostgreSQL? |
| [Browser journeys](../tests/e2e/test_workshop.py) | What is observed in the UI, and what remains outside the journey? |
| [Coverage configuration](../pyproject.toml), [workflow](../.github/workflows/delivery.yml) | What is measured, excluded and enforced? |

Measured **Python `app` line and branch coverage** must reach 100%. React, migrations and host/deployment scripts are outside that measurement. Explicit exclusions include operational CLI bodies, server lifecycle/mail-loop orchestration and ASGI disconnect exception handling; operational/browser evidence supplements them. That evidence is not a claim that every possible lifecycle path has been tested. The complete exclusion policy matters as much as the number. Coverage measures execution, not assertion quality, security or correct requirements.

CI runs integration tests against PostgreSQL and three browser journeys against the exact release image with a mock provider. Real model traffic and actual inbox receipt require separate authorized verification. Image scanning blocks fixable HIGH/CRITICAL findings; a passing gate does not establish that all vulnerabilities are absent.

## Running safely and interpreting results

The integration suite deletes application data in its target database. The guard in [tests/targets.py](../tests/targets.py) rejects remote PostgreSQL targets, requires a loopback host and a database name ending in `_test`, and requires `TEST_ALLOW_RESET` to equal that exact name before migration/reset. SQLite must live under the test's temporary root. These checks reduce target mistakes; the operator still supplies a dedicated disposable database. Follow [Lab 07](labs/07-admission-and-coverage.md) rather than substituting a familiar database.

The local browser harness creates a temporary database and test-only server on loopback port 9001. Before browser writes, it verifies a per-run nonce plus mock-provider/disabled-email identity; public URLs are refused before a network client is created. [Lab 06](labs/06-browser-accessibility.md) uses that harness and treats its public fixture password as test data. This safety improvement addresses the original [#11](https://github.com/kaw393939/is373-ai-chat/issues/11) finding; it is separate from proving the app secure.

Development, CI and the image pin Python 3.14.7. An earlier local comparison found passing tests with a differing 3.13 coverage trace around asynchronous database operations. This is an observed case-study discrepancy, not a general claim that Python 3.13 coverage is defective. Preserve alignment and investigate measurement differences rather than adding exclusions to hide them.

**Evaluate:** show a failing regression, its smallest repair, and a rejected test that would have provided weaker evidence. Explain one failure the passing suite could still miss. Unknown provider termination, cross-tab refresh and keyboard-dialog behavior remain visible backlog work rather than inferred guarantees from 100% coverage.
