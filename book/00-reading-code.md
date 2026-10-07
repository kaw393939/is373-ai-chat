# Reading code as a textbook

An engineer reads code to understand a promise: what enters, what is allowed, what changes, what can fail and what leaves. Syntax is only part of that explanation. In this repository, start with a business question, follow the request, and inspect the boundary that makes the answer trustworthy.

Use the [reader's guide](start-here.md) to check prerequisites and choose a route. This chapter teaches a reading method; [the foundations bridge](foundations.md) introduces the vocabulary needed to apply it.

For example, “May this user read this conversation?” is answered by current authentication and a database ownership check. A valid JWT is one step in the answer. A hidden frontend button is not the answer. Read [token validation](../app/security.py), the `current` dependency in [routes](../app/main.py), and `owned` in [services](../app/services.py), then inspect [cross-account tests](../tests/integration/test_web_security.py).

## Where explanations belong

| Location | Explain | Avoid |
|---|---|---|
| Names and types | What a value or operation represents | Cryptic abbreviations and vague helpers |
| Module docstring | Responsibility and its boundary | A copied chapter or unsupported architectural claim |
| Function docstring | Contract, invariant or surprising consequence | Repeating a self-explanatory function name |
| Inline comment | Why this decision exists, especially concurrency/security/recovery | Narrating every assignment or claiming a guarantee beyond the code |
| Chapter or ADR | History, alternatives, diagrams, tradeoffs and longer reasoning | Duplicated copies of changing implementation |
| Test | A behavior that should remain true, including failure cases | Assertions that merely mirror the implementation |

Consider `digest` in [security.py](../app/security.py). A useful explanation says that refresh/recovery tokens are high-entropy random bearer secrets and only their digests are stored. It also explains why SHA-256 here is different from password hashing: human-chosen passwords need an expensive password-specific algorithm. “Hash the value” would add little understanding.

Likewise, the database factory explains why its pool is bounded and why each task needs a separate session. Its documentation does not pretend a session factory decides every transaction boundary. The use case still owns its commits and locks.

## A repeatable reading method

1. State the user's goal and identify the public entry point.
2. Name the trust boundary: browser, current account, database, provider or operator.
3. Follow inputs and durable state. Mark every validation, lock and commit.
4. Follow the failure path: rejection, partial output, timeout, cancellation or recovery.
5. Find the test and distinguish its assertion from an untested assumption.
6. Propose one small change and explain which contract it must preserve.

Comments are maintained code. When changing behavior, update the explanation in the same atomic change. A comment explaining an absent guarantee is worse than no comment because it teaches false confidence. Known gaps belong beside their limits and linked issues; they should not be disguised as completed examples of SOLID or resilience.

## Annotated reading tour

The [generated excerpts](generated/code-tours.md) provide small source-derived selections beside their explanations. Use them to enter the actual functions, not to replace reading their callers and tests. Record the checkout with your evidence: an excerpt from one source revision cannot establish a later deployment's behavior.

| Read | Question | Evidence |
|---|---|---|
| [Security](../app/security.py) | Why specify algorithm, issuer, audience and expiry? | [Unit tests](../tests/unit/test_security.py), [pilot lab](labs/01-token-boundaries.md) |
| [Database factory](../app/db.py) | What is shared, what belongs to one task, and what bounds connections? | [Data chapter](03-data.md) |
| [Provider contract](../app/providers.py) | What can be substituted, and what remains provider-specific? | [Adapter tests](../tests/unit/test_providers.py) and [durable terminal-state tests](../tests/integration/test_terminal_state.py) |
| [Admission and sessions](../app/services.py) | Why are locks and commits part of correctness? | [Concurrency and chat tests](../tests/integration/test_chat.py) |
| [Deployment wrapper](../deploy/chat-deploy) | Why might restoring an old image be unsafe after migration? | [Delivery](08-delivery.md), [recovery](10-recovery.md), [setup fault tests](../tests/deployment/test_candidate.py) |

The goal is readable production code with enough explanation to teach a decision, supported by a book that has room to discuss its history and consequences.

## Worked reading question

Read `decode_token` and write its contract before opening the surrounding routes: which algorithm is accepted, which issuer/audience are expected, which claims are required, and which failures become HTTP 401? Then read `current`. Its database checks answer a different question: is that signed identity still allowed now? Finally read `owned`: which actor may use this particular conversation?

Now supply a counterexample to each layer alone. A signed token may be expired. A valid token may identify a revoked family. An active account may request a different account's conversation. This is why “the JWT is valid” cannot substitute for the complete request trace. [Lab 01](labs/01-token-boundaries.md) makes one counterexample executable; [Lab 04](labs/04-ownership.md) investigates the resource boundary.

When commenting a change, state the reason a reviewer could otherwise miss. “Refreshes are serialized” is too broad for the current client. “Web Locks serialize cookie mutations among cooperating same-origin contexts; an opaque epoch invalidates stale work, while bearer secrets stay in tab memory” identifies the actual scope. Unsupported locking/storage causes a visible refusal; it does not establish coordination with an unrelated client or malicious script. Comments should help the next engineer choose a safe change, not advertise an unproved guarantee.
