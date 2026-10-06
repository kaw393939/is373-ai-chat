# Implementation evidence

Recorded October 6, 2026. Executed checks are separate from remaining operational work.

## Tests and release

- 34 unit/integration tests passed against PostgreSQL 17, including concurrent admission. Measured Python application line and branch coverage is 100%; the metric does not include React or host scripts.
- CLI operation bodies, ASGI disconnect exception handling and lifespan cleanup have explicit coverage exclusions. CLI/bootstrap/pruning, cancellation and container startup have separate execution evidence.
- Two Python Playwright journeys passed against the exact release image: registration/approval/history/refresh/CRUD and admin budgets/cancellation. TypeScript compilation, formatting, Python lint and Alembic schema parity passed.
- Docker builds one release artifact. Subsequent jobs publish and deploy its digest without rebuilding; image and public health commit identities are checked.
- Full Trivy findings and CycloneDX SBOM are saved as CI artifacts. The gate blocks fixable HIGH/CRITICAL findings. Unfixed findings still require review. The hardened image report showed zero fixable findings and no detected secrets; eight unique unfixed HIGH Debian advisories appear across 44 package records. These chiefly concern util-linux/mount, ACL, ncurses, systemd and Perl components. Non-root/no-new-privileges/capability restrictions reduce privileged-operation exposure; they are not a blanket vulnerability waiver.
- Development, CI and the image use Python 3.14.7. Tests also passed on 3.13, whose tracing reported incomplete execution around async database operations; no coverage exclusions were added for that discrepancy.

## Production exercises

- Initial HTTPS deployment on chat.mywebclass.org, then moved to the requested [firehose360.com](https://firehose360.com). Its priority-100 chat router takes precedence over the preserved original Apache apex route.
- Playwright verified admin login, a real streamed OpenAI response, history after reload/refresh, conversation deletion and logout; no browser errors were recorded. The real-provider/browser journey also passed on firehose360.com after the move.
- A separate browser check waited for real account/budget data and live CPU/memory/disk/container metrics, then inspected the dashboard screenshot.
- Computer Use also verified login, loaded administrative budgets and live host/container metrics, and logout on the final release in the user's browser.
- Admin bootstrap and password replacement ran without committing credentials. The restricted deployment SSH key rejected an ordinary shell command.
- Metrics timer active; daily backup/pruning service ran successfully. A daily dump restored into a disposable database with matching schema `0001`, one user, two roles and one daily usage row; the disposable database was removed.
- Controlled app restart preserved accounts, usage and schema, and readiness returned healthy.
- Docker inspection confirmed app user `10001:10001`, read-only root, all capabilities dropped, 512 MiB, 0.75 CPU, 128 process limit and no published host ports.
- Existing classroom and calculator HTTPS endpoints returned 200 after installation. Temporary test database and development services were cleaned up.

## Final release identity

The final application release passed verification, publication and deployment in [run 37525424445](https://github.com/kaw393939/is373-ai-chat/actions/runs/37525424445). Public HTTPS health independently returned the matching source commit, healthy status and schema `0001`.

- Source: `d3e576a053bdaeb51bb491897bd11c90270203ca`
- Image: `ghcr.io/kaw393939/is373-ai-chat@sha256:8a1f00224a965a105b2b1d9ea2e572e506fdc71d167e2aa8256c88a22f1e0f21`
- Application: [firehose360.com](https://firehose360.com)

Later documentation-only commits do not change this deployed application identity. The first complete deployment is independently recorded in [run 37523682890](https://github.com/kaw393939/is373-ai-chat/actions/runs/37523682890).

## Remaining operational work

Single amd64 server and app process; releases have a short interruption. Admin approval and admin-issued recovery replace automated email. Text streaming only. Reservation units are conservative admission accounting rather than provider billing. Backups are local until an off-host destination is configured. DigitalOcean account-side backup/firewall/alert settings remain unverified, and fresh-droplet installation has not been independently rehearsed. The one-day app credential lease ends October 7, 2026 at 19:58 UTC and does not revoke the key at the provider.
