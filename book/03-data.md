# 3 · Durable state and schema changes

[Models](../app/models.py) represent users, sessions, hashed refresh/recovery tokens, role budgets, conversations, messages, generation state, daily reservations, rate-limit buckets and audit events. Foreign keys with database cascades make ownership and deletion explicit.

[Migration 0001](../migrations/versions/0001_accounts_chat_budgets_sessions_and_audit.py) is a frozen schema definition. It does not import today's models and call create_all: doing that would silently change what an old migration means after a model edit.

```sh
uv run alembic revision --autogenerate -m 'describe the schema change'
# Read and edit the generated migration.
uv run alembic upgrade head
uv run alembic check
```

Autogeneration proposes changes; it cannot infer every intent, including many renames. Review SQL and compatibility before release. CI checks drift against a migrated PostgreSQL database.

A transaction is a consistency boundary, not the entire lifetime of an HTTP request. Chat admission locks a shared budget row, validates limits, reserves capacity, saves the prompt/run, and commits. Streaming does not hold that transaction open while waiting on an LLM. Short later transactions persist completion/cancellation.

One AsyncSession belongs to one task. Share the session factory, not a session. Connection pools are bounded. PostgreSQL row locks serialize admission across workers; SQLite is useful for fast tests but cannot prove those semantics.

**Exercise:** write an additive migration, deploy it, and explain which previous app versions remain compatible. Do not treat schema downgrade as an automatic recovery strategy.
