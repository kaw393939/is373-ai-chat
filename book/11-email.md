# 11 · Email is a delivery boundary

An account request can commit to PostgreSQL while its email fails to reach a sender. Sending first can produce a link for a transaction that later rolls back. Sending afterward can lose the message if the process crashes in between. This dual-write problem is the reason for an outbox, not simply a reason to add another library.

**Learning outcomes:** distinguish address verification from approval; trace a database-to-provider failure; explain idempotency and bounded retries; separate local adapter evidence from actual delivery/DNS proof. Read [transactions](03-data.md), [identity](04-auth.md) and [recovery](10-recovery.md).

## A pattern for an older coordination problem

Chris Richardson's transactional-outbox account describes committing an outgoing message with business data, then using a relay to send it. It also explains that the relay can send twice if it crashes before recording acceptance. The pattern addresses lost coordination without supplying universal exactly-once delivery. Our application adapts that idea to email rather than deploying a microservice system. [Original pattern account](references.md#ref-outbox).

A synchronous send can be simpler for a disposable prototype, but couples the HTTP response to external availability. A durable outbox introduces worker/key/retention responsibilities. Choose the pattern because recovery links must survive a process interruption, and explain those additional costs.

## Worked case: accepted email, lost acknowledgement

Suppose a fake sender accepts a synthetic message and the local worker loses its response. A retry must reuse the message's identity rather than generate a new link for every attempt. The request commits a hashed recovery/verification token and encrypted outbox payload together. The worker later locks a pending row and sends with `chat-email/` plus its stable row ID as the provider idempotency key.

The worker holds a database row lock/transaction around its bounded HTTP send. That simplifies coordination but consumes a connection while waiting, unlike chat admission's transaction-free streaming interval. A larger workload may justify a lease/claim design; it would need recovery rules for abandoned claims. Keeping this cost explicit prevents the outbox from appearing free.

Resend's documented idempotency window bounds what that provider guarantee means. Row locks coordinate this database's workers, while the stable key addresses repeated provider requests; neither proves exactly-once inbox arrival across every failure. The worker deliberately bounds each batch to ten and attempts to six. After delivery, expiry or exhaustion it erases the payload; metadata remains temporarily for quotas. [Sender idempotency](references.md#ref-resend-idempotency).

Fernet authenticated encryption protects pending recipient/link payloads at rest under a separate operator key. The token lookup stores a digest. Delivered payload erasure reduces retained sensitive data; it does not erase a recipient's mailbox or historical external-provider records. Rotating the key before pending messages drain makes them unreadable. [Fernet](references.md#ref-fernet).

## Read the implementation

| Symbol/file | Question |
|---|---|
| [`token_email`, `enqueue`](../app/email.py) | Which link and payload changes must commit together? |
| [`drain`, `ResendMailer.send`](../app/email.py) | What survives retries, and when is payload erased? |
| [`consume_link`](../app/services.py) | How do expiry, one-time redemption and sibling invalidation cooperate? |
| [Email tests](../tests/integration/test_email.py) | Which fake transport, quota, retry and concurrent redemption cases are asserted? |
| [DNS audit](../docs/audit/2026-10-06-dns.md), [email options](../docs/email-options.md) | Which receiving and sender-authentication facts remain external? |

Verification proves access to an address; admin approval grants use of the app. Existing approved accounts survive migration `0002`; new accounts verify when email is enabled. Recovery links expire in 30 minutes and use URL fragments to avoid putting bearer values in ordinary request paths/access logs. Origin, single-use and authorization protections remain necessary.

Quotas permit 80 queued messages per UTC day and 2,000 over a rolling 30 days, with anonymous IP/address limits. Generic recovery responses reduce account disclosure, but saturation/eligibility response ordering remains [#15](https://github.com/kaw393939/is373-ai-chat/issues/15). Do not infer complete enumeration resistance from one generic success message.

## External delivery and limits

Resend uses HTTPS and Reply-To routes human replies to the existing inbox; another paid Google mailbox is not required for a sending-only address. Preserve apex Google MX routing. SPF authorizes senders, DKIM signs messages, and DMARC states alignment/reporting policy; a working API call does not verify all three or inbox placement. Enable the protected sender configuration only after domain/key verification. Real production sending and actual receipt remain [#3](https://github.com/kaw393939/is373-ai-chat/issues/3); CI uses mock delivery without paid sender credentials.

**Laboratory:** [Lab 11 — email outbox](labs/11-email-outbox.md), using fake transport and synthetic recipients. **Evaluate:** draw the failure window, justify a stable idempotency key, and distinguish provider acceptance, message receipt, address verification and account approval.
