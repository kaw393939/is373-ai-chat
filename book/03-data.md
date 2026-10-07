# Durable data: preserve meaning while software changes

The list API supports opt-in `page=true&limit=50&cursor=...&q=...`, returning `items` and `next_cursor`. Legacy list calls retain arrays. Cursor selection uses `(created_at,id)` descending so equal timestamps remain deterministic; signed cursors bind the account and search filter. Search is a literal substring in owned conversation titles or administrator account emails. History initially returns the most recent fifty messages/runs, with separate older-page cursors and owned `/messages` and `/runs` endpoints. Each message batch is chronological for display. New writes can appear before an existing cursor; unchanged datasets have no duplicates/skips. The [executed PostgreSQL plan review](../docs/audit/2026-10-06-pagination-plans.md) retains existing indexes for the current release and records the growth limits.

A new enrollment feature needs verified email addresses. The application already has approved users, and a deployment must not silently turn them into locked-out students. This is a data-design problem before it is a migration command.

After this chapter, you should be able to distinguish an ORM model from a historical migration, explain a short transaction boundary, review a real additive migration and state which compatibility questions need a rehearsal. [Lab 03](labs/03-migration.md) applies these ideas to another synthetic change.

## From rows to objects without losing the database

An application could issue parameterized SQL and map rows manually. SQLAlchemy supplies query expressions, mapped objects and session/unit-of-work behavior. It changes Python's interaction with the database; it does not make constraints, isolation or query costs disappear. The [historical chapter](12-history.md#from-files-and-pointers-to-relational-data) discusses the problem this abstraction addresses.

Read the [models](../app/models.py) as promises about durable state:

| Structure | Promise or relationship | What it does not decide |
|---|---|---|
| Unique `User.email` | Two committed users cannot share that stored address. | Whether a request should reveal an address exists. |
| `Conversation.user_id` foreign key | A conversation refers to an existing user. | Whether the requesting user may read it. |
| Message/conversation cascade | Deleting a conversation deletes its dependent messages. | Whether deletion is an acceptable retention policy. |
| Unique generation `(user_id, request_key)` | An account/key pair cannot create two persisted generations. | Whether a provider billed an interrupted attempt. |

Constraints protect relationships even when an application path is wrong. Server authorization protects which actor may request an operation. They are complementary boundaries.

## A small page can require a large scan

Returning fifty messages bounds the response, not the work needed to find those messages. In the synthetic review, the first owner conversation page reads 2,000 matching rows, sorts them and returns a 51-row probe. The long-conversation message page scans 20,000 table rows, retains 5,000 matching messages and orders the newest probe. The missing email substring examines all 5,000 synthetic accounts and returns none. Rare output is not necessarily cheap input.

Read the plan from its scan toward its parent sort and limit. `Actual Rows` describes rows emitted by a node; `Rows Removed by Filter` helps explain rejected candidates. Do not add every parent's count together as if each represented another table read. An ownership index can narrow candidates without supplying `(created_at,id)` order. A sequential scan can be the cheaper plan for a large matching fraction. PostgreSQL's [EXPLAIN guide](https://www.postgresql.org/docs/17/using-explain.html) explains these distinctions.

All fifteen observed probes returned at most 51 rows; their single-run query times were below 39 ms on temporary relations. Those observations support a modest teaching workload, not a production latency or concurrency promise. The [guarded helper](../tests/integration/pagination_plans.py) reproduces plans with synthetic data and no public-table writes. At larger histories, compare ordered composite indexes and actual cursor conditions; substring search needs its own evaluation. An index is a measured storage/write/read tradeoff, rather than a decoration added to every filter.

<a id="migration-0002"></a>

## Worked change: migration 0001 → 0002

The real [migration 0002](../migrations/versions/0002_verified_email_and_outbox.py) introduces email verification, purpose-bound recovery links and an outbox. Its predecessor is explicitly `0001`. It contains schema operations rather than importing today's models and recreating them. Otherwise a model edit could silently change what replaying an old migration means.

| Before, schema 0001 | After, schema 0002 | Reason |
|---|---|---|
| No user verification column. | Non-null `email_verified`, database default true. | Existing administrator-approved accounts retain access policy. |
| No recovery purpose column. | Non-null `purpose`, default `reset`. | Existing recovery links retain their meaning. |
| No durable email work table. | New `email_outbox` table and status index. | Committed delivery work survives process replacement. |

Default true is a migration policy, not proof that every historical user controlled an inbox. New registration explicitly sets verification false when mail is enabled; mail-disabled local registration sets it true. Read `register` in [routes](../app/main.py) alongside the migration to understand these populations. A schema change alone cannot enforce enrollment.

Review PostgreSQL SQL without connecting to a database:

```sh
DATABASE_URL=postgresql+asyncpg://chat:synthetic-lab-only@localhost:5432/chat \
  uv run alembic upgrade 0001:0002 --sql
```

The URL is deliberately synthetic. `--sql` renders operations offline; it does not apply them. The explicit dialect matters: a local SQLite URL produces different SQL. Selected generated PostgreSQL statements are:

```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT true NOT NULL;
ALTER TABLE recovery_tokens ADD COLUMN purpose VARCHAR(16) DEFAULT 'reset' NOT NULL;
CREATE INDEX ix_email_outbox_status ON email_outbox (status);
UPDATE alembic_version SET version_num='0002'
WHERE alembic_version.version_num = '0001';
```

Complete output also creates the outbox and includes transaction boundaries. This is a code-derived reading example, not SQL to paste into production. The revision table records schema history; it does not establish business correctness, delivery or recovery.

## Why autogeneration is a proposal

Alembic compares database schema with model metadata. It proposes additions and removals but cannot infer all intent: a rename can look like dropping one column and adding another. Candidates require review. [Alembic's documentation](https://alembic.sqlalchemy.org/en/latest/autogenerate.html) makes this distinction explicit.

For a new change on a learner branch, point `DATABASE_URL` at disposable local PostgreSQL, update the model, then generate and inspect a candidate:

```sh
uv run alembic revision --autogenerate -m 'describe the intended change'
# Review the created migration and its SQL before applying it.
uv run alembic upgrade head
uv run alembic check
```

`alembic check` uses the configured metadata comparison and fails when it detects proposed schema differences. It does not prove records or old clients survive. Our [migration environment](../migrations/env.py) compares types but does not enable server-default comparison; a clean drift check does not validate every default.

## A transaction follows the invariant

For chat admission, “check remaining budget” and “consume budget” must form one decision. If two requests independently see capacity and both spend it, a limit has not been enforced.

`prepare_run` in [services](../app/services.py) locks a shared role-budget row, loads current policy and locks the user/conversation. It checks duplicate keys and concurrency, computes a conservative reservation, updates daily usage, saves the prompt and empty assistant message, creates the generation, and commits before returning to the streaming route.

| Time | Durable state | Locks / external work |
|---|---|---|
| Before admission | No new prompt or reserved run. | Auth, ownership and policy checks must pass. |
| During admission | Changes are within one transaction. | PostgreSQL locks serialize conflicting decisions. |
| After admission commit | Prompt, placeholder, generation and reservation exist. | Model streaming begins without retaining the admission transaction. |
| Finalizing output | Later short transactions persist results. | External waits do not need one long transaction. |

Extending admission across a two-minute model call would retain locks/connections while unrelated users wait. Separating reservation and generation commits would instead create partial outcomes. The business invariant determines the boundary, not the HTTP request's duration.

The [database factory](../app/db.py) bounds its PostgreSQL pool at five connections per app process, with no overflow. Each task gets a separate mutable session; the factory and pool are shared. Replicas multiply this budget. SQLAlchemy documents [one AsyncSession per concurrent task](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks). `expire_on_commit=False` permits reading committed objects without implicit reload; it does not make those values perpetually current.

SQLite is useful for fast isolated tests. Its behavior cannot establish PostgreSQL row-lock correctness. Use PostgreSQL integration/concurrency evidence for that claim.

## Who owns each unit of work?

The route validates transport inputs and translates `DomainError` kinds to HTTP status codes. `accounts.py` owns registration, link verification, password changes and administrative access edits. `mfa.py` owns factor/challenge state; `services.py` owns session/admission/generation operations. Helpers such as `revoke_all`, `owned` and `consume_link` participate in their caller’s unit rather than committing independently. This is a function-based unit of work using SQLAlchemy’s session, without a generic repository hierarchy.

| Unit | Commit owner | Failure boundary |
|---|---|---|
| Attempt throttling | A separate short factory/session in `throttling.py`. | Rejected attempts persist; unrelated caller mutations cannot be committed. |
| Authentication read | `current` finishes its read-only unit. | Releases the pooled connection before independent throttling. |
| Registration | `register_account`. | User, link and outbox roll back together. |
| Approval/access edit | `edit_account`. | Actor revalidation, edited access, revocations, notice and audit share one commit. |
| Refresh | `rotate`. | Replacement commits; reuse revocation deliberately commits before refusal. |
| MFA verification | `verify_challenge`, then `new_session`. | Consumed factor and assured session commit together; rejected guesses commit only attempt count. |
| Password/link changes | Account use case. | Token use, account mutation, session revocation and audit share one commit. |
| Chat admission | `prepare_run`. | Fresh locked account/session authority, reservation and initial transcript commit before external I/O. |
| Streaming finalization | `generate`. | A shielded later short unit persists terminal state and partial text. |

The [transaction-boundary tests](../tests/integration/test_transaction_boundaries.py) prove independent attempts cannot commit pending account work and exhausted approval mail rolls back approval, revocation and audit together. PostgreSQL races prove the lock-based claims; SQLite alone does not.

## Compatibility and recovery are separate decisions

Adding columns and a table often supports an expand-first release: old code ignores additions while new code uses them. That is a hypothesis to test, not a blanket guarantee. Compare old writers, new defaults, verification policy and outbox-worker behavior. An old binary may ignore pending mail even if its queries still run.

This migration's downgrade removes the outbox and added columns. It reverses schema operations by discarding introduced data; it does not restore prior business history. Dropping pending delivery work can affect users. Review [recovery](10-recovery.md), rehearse on disposable data and choose based on schema/app compatibility and backup evidence.

For Lab 03, preserve a synthetic old record, apply an additive change, demonstrate new behavior and explain one old-version compatibility risk. Submit SQL review, assertions, source revision and a recovery argument. A passing drift check alone is insufficient acceptance evidence.
