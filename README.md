# 373 · Chat workshop

A small, complete system you can run, test, deploy, and explain: React + TypeScript, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker Compose, and GitHub Actions. Follow a request from browser login to a streamed model response, then follow the same code into a tested production image.

Production: [firehose360.com](https://firehose360.com). Registration requires administrator approval.

## Project visibility

[Project hub](docs/project/README.md) links the educational baseline, live GitHub backlog, acceptance criteria and atomic delivery agreement. Follow a requirement through an issue, commits, tests and release evidence.

## Start locally

Install Docker, Python 3.14.7 with [uv](https://docs.astral.sh/uv/), and Node 24 for the optional source workflow. Docker supplies build runtimes when using Compose.

```sh
cp .env.example .env
docker compose up -d --wait db
docker compose build app
docker compose run --rm app alembic upgrade head
docker compose run --rm app python -m app.cli seed
docker compose run --rm -it app python -m app.cli admin --email admin@example.org
docker compose up -d --wait app
```

Open [localhost:8000](http://localhost:8000). The admin command prompts for a password; no default admin is installed. Registration requires admin approval. The mock provider makes the whole workflow usable without a paid API key.

For source development, `uv sync --frozen`, `npm --prefix frontend ci`, `npm --prefix frontend run build`, then `make migrate`, `make seed`, and `make dev`. PostgreSQL runs in Compose; DATABASE_URL in local .env points to its loopback port. Run `npm --prefix frontend run dev` for frontend reload; its proxy keeps API requests on the same browser origin. Set BASE_URL=http://localhost:5173 for that frontend workflow.

## What is included

- Registration, admin approval, login/logout, short-lived JWT access, rotating refresh sessions with reuse detection, password change/recovery, role checks and session revocation.
- Owned conversation history, search by title, rename/delete, streamed replies, stop/retry, safe text/code rendering, and interchangeable mock/OpenAI/OpenAI-compatible adapters.
- Role budgets and user overrides, atomic admission limits, conservative daily reservations, model enable/disable controls and an administrative audit trail.
- An admin resource dashboard fed by a separate host collector; container CPU/memory/process/log limits; no Docker socket in the app.
- Reviewed migrations, unit/integration tests, Python Playwright journeys, measured 100% Python `app` line/branch coverage with documented exclusions (frontend and host scripts are outside the metric), image vulnerability gate, SBOM, digest deployment and public release verification.
- Protected production configuration, a restricted deployment key, pre-deploy/daily PostgreSQL dumps, and explicit recovery rules.

## Read the textbook

Start with [From Request to Release](book/README.md): historical context, engineering contributors, code-reading guidance, laboratory map and assessment. The [glossary](book/glossary.md) and [bibliography](book/references.md) clarify terminology and original sources. The technical chapters below are the working-system spine; comprehensive chapter/lab expansion is ongoing.

The [book/course map](book/README.md) owns the reading sequence, prerequisites, chapter references and laboratory progression. Follow its links to the system, data, identity, streaming, testing, delivery, hosting, operations, recovery and email material.

## Verify

```sh
make setup
make check
TEST_DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/dedicated_test TEST_ALLOW_RESET=dedicated_test make test
make migrate
uv run alembic check
uv run playwright install chromium
# The browser harness creates and verifies its own disposable local mock server.
make test-e2e
```

Tests clear application tables only after the target guard accepts a loopback PostgreSQL database ending in `_test` and `TEST_ALLOW_RESET` equal to its exact name. Use a dedicated disposable database. Without TEST_DATABASE_URL, fast tests use isolated temporary SQLite databases; the PostgreSQL concurrency test runs in CI and with an accepted PostgreSQL test URL. Browser tests require the local disposable harness identity and reject public targets before connecting.

[Delivery workflow](.github/workflows/delivery.yml) verifies amd64 only. [Deployment evidence](docs/implementation-evidence.md) records actual checks and remaining operational limits. Production host installation is authorized for this project; deployments are separate from the existing calculator.

## Background and boundaries

[Original server audit](docs/system-audit.md), [recreation of the prior classroom host](docs/recreate-observed-host.md), and [research decisions](docs/references-and-decisions.md) preserve how the project started. They describe the earlier server state; current application behavior is explained in the textbook and code.

This is a single-server teaching deployment. It does not claim high availability, independently verified account-side backups, unrestricted provider feature parity, attachment/RAG/tool execution, or exact dollar billing. Automated email requires sender activation; admin-issued recovery remains available. Provider configuration is controlled by the operator, not exposed to browser users. Temporary credentials require replacement when their lease expires.

[Browser review and security notes](docs/review-and-security.md) records findings, fixes and follow-up ideas.

[Low-cost email options](docs/email-options.md) explains Google aliases, a free transactional sender and the Google-only API alternative.

Public dev/QA hosting: [environment runbook](docs/environments.md) and [DNS audit](docs/audit/2026-10-06-dns.md).

## Reuse

Original software is [MIT licensed](LICENSE). Original book prose and diagrams and educational prose in `docs/` use [CC BY 4.0](LICENSE-CONTENT); source excerpts and fixture programs remain MIT. See [NOTICE](NOTICE) and [publication notes](book/publication.md) for attribution, AI-assistance disclosure and third-party boundaries.
