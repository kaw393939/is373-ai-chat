# PostgreSQL pagination and search plan review

Observed October 6, 2026 (America/New_York; recorded October 7 at 01:08 UTC), for [#20](https://github.com/kaw393939/is373-ai-chat/issues/20). This is a **source query-plan review on synthetic temporary tables**, not production profiling or sustained-load acceptance. No application code, index or migration changed.

The [machine-readable evidence](2026-10-06-pagination-plans.json) records PostgreSQL 17.11, schema `0003`, source commit and hashes, generated SQL, settings and all fifteen `EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)` plans. The [helper](../../tests/integration/pagination_plans.py) captures SQL built by the actual `page_rows` function, using the same model selections and owner/search predicates as the routes. It validates a loopback `*_test` database and exact reset acknowledgement before connecting. It copies migrated column/index definitions into connection-local temporary tables, writes only `pg_temp`, checks name resolution and public row counts, and closes the connection to remove its fixtures. `LIKE INCLUDING ALL` does not copy foreign keys; fixture relationships are consistent, while HTTP ownership has [separate regressions](../../tests/integration/test_pagination.py).

The successful fixture contains 5,000 users, 10,000 conversations, 20,000 messages and 5,000 generations. A heavy owner has 2,000 conversations; one long conversation has 5,000 messages and 2,000 runs. A regular owner has 81 conversations. Four rows share each timestamp. Common, rare and missing literal substrings test search selectivity. Queries request fifty items plus one cursor probe. The rehearsal database has a 192-MiB memory cap; this helper uses session `work_mem=512kB` and `temp_buffers=1MB`, without disabling any scan strategy.

| Query | Chosen row scan | Rows examined by that scan | Rows returned | Execution ms |
|---|---|---:|---:|---:|
| Owner conversation first page | Bitmap heap | 2,000 | 51 | 2.406 |
| Owner conversation deep page | Bitmap heap | 2,000 | 51 | 1.339 |
| Regular owner first page | Bitmap heap | 81 | 51 | 0.778 |
| Owned messages first page | Sequential | 20,000 | 51 | 9.977 |
| Owned messages deep page | Bitmap heap | 5,000 | 51 | 3.103 |
| Owned runs first page | Sequential | 5,000 | 51 | 3.233 |
| Owned runs deep page | Sequential | 5,000 | 51 | 2.320 |
| Administrator first page | Sequential | 5,000 | 51 | 9.428 |
| Administrator deep page | Sequential | 5,000 | 51 | 3.117 |
| Conversation common search | Bitmap heap | 2,000 | 51 | 4.199 |
| Conversation rare search | Bitmap heap | 2,000 | 1 | 2.160 |
| Conversation missing search | Bitmap heap | 2,000 | 0 | 2.968 |
| Administrator common search | Sequential | 5,000 | 51 | 38.134 |
| Administrator rare search | Sequential | 5,000 | 1 | 9.068 |
| Administrator missing search | Sequential | 5,000 | 0 | 8.607 |

“Examined” here is the row-producing scan's actual rows plus rows removed by its filter; it does not add its bitmap-index child's rows a second time. Top-N sorts used 38–51 KiB; tiny/empty matches used quicksort. The rare conversation query returns one row after rejecting 1,999 owned rows. The message first page examines all 20,000 rows because this fixture's heavy conversation is a substantial fraction of the table. A sequential scan is a cost-based choice, not evidence that an index was ignored incorrectly. PostgreSQL explains these [scan, filter and sort distinctions](https://www.postgresql.org/docs/17/using-explain.html).

These single sequential observations do not establish HTTP latency, cold-cache behavior or throughput. Temporary relations use local buffers and cannot establish production cache/parallel behavior. A larger first fixture lost its connection; the coordinator confirmed the disposable database's memory limit caused the interruption and recovery. That failed attempt is excluded from the timing table. The smaller successful fixture and explicit memory settings fit the existing rehearsal budget.

Retain the existing indexes for this low-traffic release. Bounded responses solve reachability and payload growth; they do **not** promise constant database work. Revisit plans under realistic distributions and concurrency when recorded latency exceeds an agreed budget or owned histories grow substantially. Compare `(user_id, created_at, id)` conversation and `(conversation_id, created_at, id)` history indexes, including deep cursor conditions, before proposing a migration. Account ordering needs its own comparison. Leading-wildcard substring searches require a separate decision: PostgreSQL's [multicolumn B-tree rules](https://www.postgresql.org/docs/17/indexes-multicolumn.html) and [trigram search support](https://www.postgresql.org/docs/17/pgtrgm.html) describe different capabilities. Measure write/storage costs as well as read improvement; no extension is enabled here.

To reproduce, migrate a **disposable loopback PostgreSQL** database through the normal lab setup, then supply its private connection value and exact name:

```sh
# TEST_DATABASE_URL identifies the already prepared local *_test database.
# TEST_ALLOW_RESET must equal its database name; neither value is printed.
uv run python -m tests.integration.pagination_plans --output .state/pagination-plans.json
```

The helper does not create a database or migrate a target. A database name alone is insufficient: remote hosts, missing acknowledgement and unsupported drivers fail before connection. Evidence must identify its actual source/settings/data, rather than treating this historical timing table as a future benchmark threshold.
