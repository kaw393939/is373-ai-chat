# Laboratory desk: start here

These labs teach explanation, diagnosis and justified change in a learner-owned checkout. Commands below target macOS/Linux terminals or a Linux shell in Windows. Use the book edition's recorded code baseline; record `git rev-parse HEAD` with each submission. A maintainer command check is distinct from an independent human learner pilot, which remains pending.

## One preflight, then twelve investigations

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), clone the repository into a directory you own, and run from its root:

```sh
uv sync --frozen --python 3.14.7
git rev-parse HEAD
uv run python --version
```

Expected: a full source SHA and Python 3.14.7. The locked environment supplies pytest, coverage, Alembic and Playwright. Docker is needed only for the container/PostgreSQL extensions, image lab and recovery lab. Check `docker version` before those activities. `uv run playwright install chromium` prepares Lab 06. Network access can be needed to install locked tools or pull/build images; no hosted model key, mail key or paid cloud instance is needed.

The bounded [fixture program](fixtures.py) creates temporary experiments and prints asserted checkpoints. Read the named function before running it. Its PostgreSQL modes create their own labeled container, publish a random **loopback-only** port and delete only that container's ID/anonymous volumes on exit. They do not accept a server URL. They require an operator-owned local Docker daemon; a remote `DOCKER_HOST` is not a classroom shortcut.

For the test commands in these labs, `env -u TEST_DATABASE_URL -u DATABASE_URL` selects pytest's temporary SQLite fixture. App configuration and credentials are scrubbed by the test fixtures. PostgreSQL locking evidence comes from the dedicated `admission` fixture, which sets its own loopback `lab_test` URL and explicit reset marker. Public dev/QA/prod are not test targets. The browser harness additionally checks its local origin and unique run marker before any journey.

## Your evidence notebook

For every lab, submit one short Markdown record:

```text
Lab / source SHA / OS and tool versions:
Prediction before running:
Command and observed checkpoint:
Boundary or invariant the result demonstrates:
Fixed fault, cause and smallest repair:
What this evidence does not establish:
Transfer problem / rejected alternative:
AI assistance and a correction or independently checked claim:
```

Screenshots support an explanation; a screenshot alone does not explain causation. Do not paste real secrets, account details, access tokens or provider responses into evidence. Synthetic identifiers can be included. A result that differs from the expected checkpoint is evidence to diagnose, not permission to loosen the assertion.

## Change and cleanup rules

A guided fixture's failure is expected and contained. A transfer change belongs in a private learner fork or disposable local branch. Commit only that lab's relevant files; inspect `git diff` before committing. Do not push a broken exercise to the application's main branch. Do not disable authentication, target checks or production settings to make a test pass.

The temporary fixtures clean themselves. Pytest removes its temporary test databases through normal temporary-directory management; evidence can remain in `artifacts/`. The browser harness stops its own server and deletes its temporary database. Image work removes only the unique lab tag you created; do not prune Docker globally. If interrupted by a hard kill, use `docker ps --filter label=is373.book-lab` to identify the lab container, verify its label, and remove that exact ID. Never substitute the application's production project or use `down -v` as a universal cleanup command.

## Trouble at the starting line

| Symptom | Diagnosis and bounded next step |
|---|---|
| `uv` missing | Install it through the official guide; reopen the shell and repeat preflight. |
| Frozen sync fails | Record the error and check Python/platform/network availability; do not regenerate `uv.lock` to bypass it. |
| Docker missing/unavailable | Complete non-container labs first. Obtain a local engine; do not use the classroom production host as a substitute. |
| Port 9001 busy | Stop your own previous browser fixture or identify the owner. The harness should refuse an unrelated server. |
| Reset/target rejected | Keep the rejection. Use the temporary fixture or dedicated PostgreSQL wrapper; do not add production credentials. |
| A locking test skips | SQLite cannot prove PostgreSQL row locking. Run the dedicated PostgreSQL activity before claiming concurrency evidence. |

Consult the [instructor assessment guide](../instructor/README.md) for observable criteria and the [human pilot record](../instructor/pilot-record.md) for validating the teaching material itself.
