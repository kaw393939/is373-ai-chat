# 7 · Test contracts, not implementation trivia

Unit tests cover configuration, password/JWT behavior and normalization of both provider wire formats. Integration tests exercise HTTP authentication, refresh reuse, account policies, ownership, CRUD, budgets, cancellation, failures and monitoring against a migrated database. A PostgreSQL concurrency test races admission and checks that only one request succeeds.

The suite deletes test application data. Use only a dedicated disposable TEST_DATABASE_URL. The normal local fallback is temporary SQLite; PostgreSQL is the CI integration target.

```sh
TEST_DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/TEST_DB make test
```

Measured application coverage must reach **100% lines and branches**. Explicit `pragma: no cover` exclusions cover operational CLI bodies, server lifespan and ASGI disconnect cancellation: CLI/lifecycle behavior is exercised by installation/container/browser checks rather than padded unit mocks. Models/policies/routes/adapters remain measured. Coverage measures execution, not security or correctness; retain meaningful assertions.

Python Playwright drives actual UI journeys: registration/approval, chat streaming, safe rendering, page reload/refresh, rename/delete/retry, cancellation and admin budget controls. CI runs these against the exact release image with PostgreSQL and a mock provider. No real API credentials enter normal CI.

For a local browser fixture, use a disposable DATABASE_URL, migrate it, run `ADMIN_PASSWORD=browser-workshop-admin-1234 uv run python -m app.cli admin`, then start Uvicorn with BASE_URL=http://localhost:9001 on port 9001. Install Chromium and run `uv run pytest tests/e2e -v`. The password is a public test fixture, never a production default.

Image scanning blocks fixed CRITICAL findings; unfixed/lower-severity findings still require review. An SBOM records components. Scan success does not establish absence of vulnerabilities.

**Exercise:** remove an ownership check and identify which test catches it. Explain why a 100% report alone would not make that change safe.
