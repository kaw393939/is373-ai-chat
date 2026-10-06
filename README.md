# IS 373: full-stack AI chat and delivery

A proposed teaching application and installation guide for a provider-independent AI chat on DigitalOcean, with SQLAlchemy, Alembic, Docker Compose, JWT authentication, registration, roles, an admin console, and GitHub Actions delivery.

**Status: research and architecture discussion, October 6, 2026.** This repository currently contains the investigation and implementation plan. The application, Docker images, migration scripts, and delivery workflows are not implemented or deployed. Installation steps below describe the intended contract; they are not runnable instructions yet.

## Read before implementation

- [Full system and Docker audit](docs/system-audit.md)
- [Recreate the observed server](docs/recreate-observed-host.md) and [captured configuration](examples/observed-host/README.md)
- [Investigation: server and existing repositories](docs/investigation.md)
- [Architecture, authentication, streaming, and frontend choices](docs/architecture.md)
- [Installation and CI/CD plan, including secret ownership](docs/install-and-delivery.md)
- [Twelve-factor and SOLID requirements, milestones, and acceptance criteria](docs/requirements.md)
- [Primary sources and discussion decisions](docs/references-and-decisions.md)

## Recommended starting point

FastAPI, a supported SQLAlchemy release using its modern ORM API, Alembic, and PostgreSQL. Use an asynchronous provider interface with interchangeable LLM adapters. Keep deployment on the existing Traefik HTTPS proxy. Compile a static frontend into the application image initially, so the server runs the API and database without a separate Node server. Frontend selection remains open for discussion.

Use short-lived JWT access tokens, rotated refresh sessions, server-enforced roles, and authenticated HTTP streaming. GitHub Actions should test the exact release image, publish it by digest, migrate the database once, deploy, and verify the public release. Database-aware deployment replaces independent image polling for this application.

## Related course repositories

- [373_hosting](https://github.com/kaw393939/373_hosting): Ubuntu, DNS, Docker, Traefik, HTTPS, and operational lessons.
- [is373_ci_cd](https://github.com/kaw393939/is373_ci_cd): calculator, tested image publication, WUD updates, release identity, and rollback.
- [is373_fall2026](https://github.com/kaw393939/is373_fall2026): Next.js/React portfolio starter and student-facing documentation.

This application can own a complete end-to-end installation guide while linking the existing hosting lessons. Existing repositories remain independent.
