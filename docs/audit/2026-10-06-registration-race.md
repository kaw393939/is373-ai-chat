# Concurrent registration privacy and atomicity

Observed October 6, 2026 (America/New_York), for [#15](https://github.com/kaw393939/is373-ai-chat/issues/15). The focused [regression](../../tests/integration/test_email_privacy.py) passed both parameter cases against the guarded, disposable PostgreSQL 17.11 `issues_test` database: **2 passed in 4.72 seconds**. Application runtime was unchanged; this adds evidence to the existing fix.

Two independent HTTP clients post the same new synthetic address. A rendezvous immediately before `AsyncSession.flush` ensures both registrations have observed its absence before either performs the real insert. The wrapper calls the original flush and records an actual database error if one occurs; it never fabricates `IntegrityError`. Mock mail configuration uses a synthetic encryption key, and no external delivery or paid provider is called.

| Initial outbox count | Actual PostgreSQL outcome | Committed new records | Public response |
|---|---|---|---|
| 0 | One unit commits; the competing insert receives SQLSTATE `23505` | Exactly one user, one purpose-bound verification link, one outbox item | Both 201; identical to the existing-address receipt |
| 80, daily capacity exhausted | Each insert proceeds after its peer rolls back; both units reject delivery capacity and roll back | No new user or link; all eighty original outbox IDs and payloads unchanged | Both 201; identical to the existing-address receipt |

The exhausted-capacity case does not require a uniqueness error: the first uncommitted row disappears on rollback, permitting its competitor's insert. That competitor must still roll back its account/link work when mail admission fails. The test checks both the shared public receipt and durable state, rather than inferring privacy from status codes alone.

Reproduce only after preparing a disposable loopback PostgreSQL `*_test` target and exporting `TEST_DATABASE_URL` plus `TEST_ALLOW_RESET` equal to its database name:

```sh
uv run pytest -q tests/integration/test_email_privacy.py::test_real_postgresql_duplicate_registration_is_private_and_atomic
```

The fixture validates its target before migrations or table reset. Ordinary temporary SQLite runs skip this PostgreSQL-specific regression; they cannot prove the unique-insert waiting behavior. The prior injected-conflict regression remains useful for deterministic rollback coverage but is not the concurrency evidence above. This scoped test does not establish timing indistinguishability, provider delivery or every possible registration workload.
