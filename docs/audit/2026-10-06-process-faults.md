# Two-process source fault rehearsal

Observed October 6, 2026 (America/New_York; recorded at 2026-10-07 01:04 UTC). This is executed **source debugging**, not release-image acceptance. The guarded harness ran two actual Uvicorn processes on fixed loopback ports 9002/9003 with their own `process_test` PostgreSQL database, synthetic ordinary accounts, a held mock provider and durable synthetic mail receipts. It neither targeted a public environment nor called a paid provider or real mail service.

The runtime `app` tree was frozen through [68ba67b](https://github.com/kaw393939/is373-ai-chat/commit/68ba67bc7f6402a9b2065e5e51876ece70f779fa) and verified unchanged after execution. The driver and test-only factory were working-tree candidates subsequently committed with this report. The [sanitized JSON](2026-10-06-process-source.json) retains the source-mode distinction; private connection values, nonce, authentication tokens and worker logs are excluded.

| Experiment | Observed result |
|---|---|
| Global race across replicas | Three simultaneous requests: two admitted, one 429 at cap two |
| User race across replicas | Two different conversations: one admitted, one 429 at cap one |
| Conversation / request replay | Same chat refused at 429; duplicate key refused at 409 |
| SIGTERM during streaming | Exit after 10.277 s; cancelled state, 49 saved characters, no active reservation |
| KILL during streaming | Actual 149.974 s lease; refusal before expiry, reclaimed 1.307 s after expiry, old run interrupted; prompt/reservation survived |
| Mail acceptance then KILL | Same key after restart; two attempts, one accepted receipt, sent outbox, encrypted payload erased |

The KILL case retained zero partial response characters. Only finalization saves generated text; abrupt loss can discard already emitted tokens. Leases reclaim capacity lazily on subsequent admission. The synthetic receipt proves the application's restart/key behavior, not an external provider's retention, availability or delivery to a mailbox.

The first unchanged graceful assertion failed: the process exited after cancellation while its generation still reported streaming with empty assistant content. [f24c5de](https://github.com/kaw393939/is373-ai-chat/commit/f24c5de) explicitly closes nested transport generators and joins their finalizers before database disposal. The complete rerun above passed without relaxing that assertion. Uvicorn's configured ten-second waiting deadline is followed by cleanup; Compose reserves a 20-second stop margin. A healthy database remains necessary for durable cleanup.

For [#8](https://github.com/kaw393939/is373-ai-chat/issues/8), this source rehearsal resolves the runtime red reproduction. CI must still run [the complete harness](../../tests/process/README.md) on the frozen `chat:ci` image before acceptance. Production promotion requires `process.json` with passed status, exact-image mode, all cases, and matching release commit/version. Attach that executed CI evidence to the immutable GitHub Release. This experiment does not establish sustained-load capacity, independent-host availability or zero downtime.
