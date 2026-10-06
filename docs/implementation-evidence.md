# Implementation evidence

Recorded October 6, 2026. This page distinguishes executed checks from planned operations.

## Executed before release

- 34 unit/integration tests passed against a dedicated PostgreSQL 17 test container through a loopback SSH tunnel. The atomic admission race passed.
- Measured application line and branch coverage: 100%. CLI operation bodies, ASGI disconnect exception handling and lifespan cleanup are explicitly excluded; CLI/browser/container checks provide separate evidence.
- Two Python Playwright journeys passed against the built React UI and mock-provider API: registration/approval/history/refresh/CRUD and admin budgets/cancellation.
- React TypeScript compilation and production bundle succeeded; dashboard screenshot inspected.
- Python lint/format checks and Alembic model/schema drift check passed.
- Temporary PostgreSQL test container removed after verification.
- Restricted deploy key and host fingerprint were configured in GitHub without printing private values. Root-owned deployment wrapper, protected production configuration and host metric timer installed.

## Release verification

Initial GitHub image-build/publication/deployment, production browser/live-provider checks, backup restoration and final image identities will be recorded after they run. No application is claimed deployed by this initial entry.

## Operational limits

Single amd64 server and app process. Admin approval and admin-issued recovery replace automated email. Text streaming only. Reservation units are conservative admission accounting rather than provider billing. Backups are local unless an off-host destination is configured. DigitalOcean cloud backup/firewall/alert settings remain unverified. A provider key's one-day app lease does not revoke it at the provider.
