# Foundations bridge: enough vocabulary to enter the system

Use this chapter to repair a specific prerequisite gap. The examples are small reading exercises, not replacements for the application. Return to the full chapters when you can explain the questions at the end of each section.

## Read a function as a decision

Consider this illustrative Python function:

```python
def can_read(owner_id, current_user_id):
    return owner_id == current_user_id
```

The parameters are inputs; equality produces a Boolean result. `can_read("alice", "alice")` is true and `can_read("alice", "bob")` is false. The name communicates a proposed policy, but the function alone neither identifies a real user nor retrieves a real conversation. Those are separate responsibilities. In the actual app, authentication establishes the current account and `owned` obtains the conversation before comparing its owner.

An `async def` function can await work without occupying its execution path while that operation waits. This makes network-bound work practical; it does not mean every line runs in parallel or that shared mutable state becomes safe. A SQLAlchemy session is mutable transaction state and belongs to one task. The [Python tutorial](https://docs.python.org/3/tutorial/) provides the language background; the [asyncio overview](https://docs.python.org/3/library/asyncio.html) explains the runtime vocabulary.

**Check:** what would be wrong with accepting `current_user_id` from an untrusted request body and calling this function directly?

## Observe HTTP before guessing at the UI

HTTP exchanges have a method, target, headers and an optional body; responses have a status, headers and a body. In this app, a browser can send `GET /api/health` and receive JSON describing database readiness and release identity. A `POST /api/conversations` asks the server to create something and requires current authentication.

Open a local browser's Network panel during a lab and inspect method, path, status and timing. Record synthetic IDs when needed; never copy real authorization headers or cookies into submitted evidence. JSON describes structured data. A response with `text/event-stream` uses a framing protocol for incremental events rather than one finished JSON document. The [MDN HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview) is a useful browser-oriented reference.

An **origin** is the scheme, host and port together. `http://localhost:8000` and `http://localhost:5173` have different origins. The source-development proxy lets the browser use one origin while the proxy forwards API requests internally. This matters to cookies and the application's Origin checks.

**Check:** why can a page render successfully while one of its API calls fails? What observation separates a routing failure from an authentication failure?

## Understand durable data and transactions

A table defines rows with columns. A primary key identifies a row; a foreign key connects it to another table. Here, a conversation's `user_id` refers to an existing user. A unique constraint can stop duplicate rows even when two application requests race. An ORM maps objects and query expressions to relational operations; it does not remove database semantics.

A transaction groups database work into a commit or rollback boundary. For example, admitting chat should reserve usage and persist its prompt/run together. Saving only the prompt and then failing to reserve capacity would leave an inconsistent outcome. Holding locks throughout a slow external reply would instead make other requests wait unnecessarily. The [data chapter](03-data.md) follows the actual choice.

An illustrative query such as `SELECT id FROM conversations WHERE user_id = :user_id` describes rows for one account. The parameter must come from authenticated state; parameterization and authorization solve different problems. For SQL vocabulary, start with the [PostgreSQL tutorial](https://www.postgresql.org/docs/17/tutorial.html).

**Check:** why can a successful SQLite test fail to establish PostgreSQL row-lock behavior?

## Separate a machine, a process and a container

A process runs code. Configuration supplies values such as an origin or database URL. An image packages the application/runtime; a container is a running instance created from it. A volume holds data independently of the replaceable app container. Compose declares how local services connect.

The name `db` resolves inside the Compose application network. The source-running Python process on your computer instead reaches PostgreSQL through `localhost:5432`. Both can reach the same local database through different paths. A port mapping exposes a container port through the host; this project's local mappings bind to `127.0.0.1`. The [local chapter](02-local.md) shows the consequences, and [Docker's container overview](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) introduces the concepts.

**Check:** if you replace the app container, what preserves conversations? If the entire computer or volume disappears, what additional recovery evidence would you need?

## Treat a diff as a reviewable claim

Git records changes in commits. A diff shows what a candidate change adds or removes. From the repository root, `git status --short` shows changed files, `git diff` shows uncommitted edits and `git rev-parse HEAD` identifies the checked-out commit. These are observations, not proof that the code works.

When a lab asks you to modify behavior, use a separate learner branch and a disposable environment. Explain what the diff claims and select a test that would fail if that claim were wrong. A commit should contain one coherent change and its necessary explanation/evidence. See the [official Git introduction](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control) and the project's [working agreement](../docs/project/working-agreement.md).

**Check:** why is a passing test against one source revision insufficient evidence about a different deployed image?
