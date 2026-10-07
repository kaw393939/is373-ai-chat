# Two replicas and process faults

This is a bounded acceptance experiment for [#8](https://github.com/kaw393939/is373-ai-chat/issues/8), separate from unit/integration coverage and the browser lab. CI runs the already built `chat:ci` image by its frozen local content ID with a read-only test fixture mount. Tests are excluded from the released image. Source-mode debugging does not establish exact-image acceptance.

The harness accepts only loopback PostgreSQL database **process_test**, `PROCESS_ALLOW_RESET=process_test`, and ports 9002/9003. It refuses occupied ports and requires the fresh nonce returned by its test-only factory before HTTP writes. Settings clear runtime configuration, use synthetic ordinary accounts, disable paid integrations and replace mail delivery with a PostgreSQL-backed synthetic receipt. Never point it at dev, QA or production; it can kill only its own generated container names/process handles. Logs stay in private temporary scratch; published evidence contains only counts, identities and observed timings.

CI creates `process_test` on its isolated service, then runs:

```sh
uv run python tests/process/experiment.py --image chat:ci
```

For a reserved source-debugging window, provision a separate disposable local PostgreSQL database, export its loopback URL and acknowledgement privately, and use `--local`. Both modes migrate/reset only that guarded database. The experiment consumes about three minutes because abrupt loss waits for the actual 150-second lease; it neither edits expiry nor replaces the clock.

| Case | Required observation |
|---|---|
| Global race | Three simultaneous requests to two replicas admit two and refuse one at global cap two |
| User race | Two different conversations across replicas admit one at user cap one |
| Conversation/replay | One active run per chat; duplicate request key is 409 across replicas |
| SIGTERM | Ten-second Uvicorn graceful deadline, bounded cleanup before Compose's 20-second stop margin, cancelled terminal state, saved partial text and no active slot |
| KILL | Prompt/reservation remain; admission is refused before the real lease expires, then marks the old run interrupted and recovers capacity |
| Mail restart | Kill after synthetic provider acceptance before outbox commit; restart uses the same key: one accepted receipt, two attempts, sent outbox, erased payload |

Abrupt loss can lose emitted text that had not reached finalization; every displayed token is not promised durable. Graceful cleanup needs a working database within the stop margin. Leases recover capacity lazily on later admission. Idempotent mail acceptance depends on the provider honoring key/retention semantics; synthetic receipt proof does not prove a real provider's availability or mailbox delivery. Replicas multiply connection pools. These cases do not establish high availability or sustained-load capacity.

The graceful fault caught a failure that ordinary disconnect tests missed: Uvicorn's shutdown cancellation left a suspended stream generator unclosed, so its finalizer never saved the partial response. The repair explicitly closes the transport's nested generators and joins tracked finalizers before disposing the database pool. This is why the experiment checks durable database state after the process exits, instead of treating a clean exit code as sufficient evidence.

`artifacts/process.json` reports mode, exact image/source/version when applicable, cases and observed timings. Treat `status=passed` from an executed run as evidence; authoring the harness/configuring CI is not completed acceptance. Keep it with release scan/SBOM and QA records.
