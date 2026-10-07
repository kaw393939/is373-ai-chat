# Public development and QA

Canonical design: [ADR 0001](decisions/0001-environments-and-releases.md). Work and acceptance: [#24](https://github.com/kaw393939/is373-ai-chat/issues/24). DNS evidence: [October 6 audit](audit/2026-10-06-dns.md).

| Environment | Hostname | Docker project / root directory | Effects |
|---|---|---|---|
| Development | dev.firehose360.com | is373-ai-chat-dev / /opt/is373-ai-chat-dev | Mock LLM, disabled email |
| QA | qa.firehose360.com | is373-ai-chat-qa / /opt/is373-ai-chat-qa | Mock LLM, disabled email |
| Production | firehose360.com | is373-ai-chat / /opt/is373-ai-chat | Production configuration |

Each preview owns its database volume, private database network, JWT key and database password. Public previews use `APP_ENV=production` for HTTPS/Secure-cookie enforcement; the environment's purpose is separate from the framework's security mode. Never copy production `.env`, user data or provider credentials into previews. Only synthetic accounts and prompts belong here.

The [preview Compose file](../deploy/compose.preview.yaml) assigns unique project, router and service names. Its explicit runtime overrides force mock chat, disabled email, empty provider keys and one concurrent generation. Each app has a 256-MiB/0.30-CPU cap; each database has a 128-MiB/0.20-CPU cap. Both use PID/log limits, with the app read-only and unprivileged. These CPU caps are ceilings, not dedicated reservations. Shared-host isolation cannot protect production from host failure or every resource-contention scenario.

For a fresh installation, choose only `dev` or `qa`, create its root directory with mode 0700, and copy `deploy/compose.preview.yaml` there as `compose.yaml`. Copy [.env.preview.example](../.env.preview.example) to `.env`, set the matching stage/hostname/HTTPS URL, the exact tested image digest, and independently generated JWT/database secrets. Use `openssl rand -hex 32` for each secret and mode 0600 for `.env`. Do not use the placeholders or a production secret. Do not point a preview hostname at the production Compose project.

Run from that directory as an authorized server operator:

```sh
docker compose config --quiet
docker compose up -d --wait db
docker compose run --rm --no-deps app alembic upgrade head
docker compose run --rm --no-deps app python -m app.cli seed
docker compose run --rm --no-deps app python -m app.cli admin --email admin@firehose360.com
docker compose up -d --wait --wait-timeout 90 app
```

The admin command prompts for a unique password; store it privately. Confirm `/api/health` over verified public HTTPS and match the source commit/schema/provider to the selected digest. Inspect `docker stats`, `free -m` and `df -h /` after each install. Retain the exact digest/commit/schema and deployment time in the environment's release record. Stop only the affected preview with `docker compose stop` if it threatens production capacity; do not remove volumes as a routine recovery step.

The initial installs were operator-driven and used the already tested production artifact with separate configuration. The new [delivery workflow](../.github/workflows/delivery.yml) implements main → tested artifact → development → QA migration/browser/smoke → acceptance; [production promotion](../.github/workflows/promote.yml) is an authenticated manual choice with a production reviewer. It reuses the current accepted QA digest without rebuilding. The private attestation binds image/version/source/schema to a completed successful main delivery run. A changed QA deployment invalidates an older selection.

GitHub environments `development`, `qa`, `production` are main-only. Production requires the owner reviewer, disallows admin bypass and permits owner self-review in this sole-owner project; it is not two-person control. Each environment has a distinct forced-command deployment key. VERSION 2.0.0 is the first formal application release; legacy 1.0.0 was untagged. The [installation/promotion runbook](install-and-delivery.md) owns exact commands, secrets, metadata and schema-aware recovery. Source-level tests/configured gates are distinct from an executed accepted promotion: link that CI/QA/production evidence before closing [#24](https://github.com/kaw393939/is373-ai-chat/issues/24)/[#25](https://github.com/kaw393939/is373-ai-chat/issues/25). Resource ceilings remain starting limits, not sustained-load capacity evidence.

## Initial installation evidence — October 6, 2026

All three public `/api/health` endpoints returned HTTP 200 with normal certificate verification, commit `d65a19c8d3cd344d31b8f01103fe5e3137a8485d` and schema `0002`. Production reported provider `openai`; dev and QA reported `mock`. The installed image is `ghcr.io/kaw393939/is373-ai-chat@sha256:9bed602fcea38a5cc0a613e8440ce2b4663cbc6838e89c93411112e41edc4997`, previously tested by [CI run 37529676892](https://github.com/kaw393939/is373-ai-chat/actions/runs/37529676892).

After both preview installations, `free -m` reported 843 MiB available out of 1967 MiB, with no swap. Native Safari verified dev and QA admin sign-in and mock streamed conversations, plus loaded development host/container metrics. QA initially had no development conversation history. API probes confirmed that dev/QA JWTs are rejected by the other preview and by production (HTTP 401); probe sessions were revoked. Server checks verified three distinct JWT/database secrets, separate preview database volumes/private networks, configured limits and disabled provider/mail effects. Preview administrators also have separate passwords stored outside version control. The new preview Compose was validated with `docker compose config --quiet` and exercised by migrations/admin setup/startup; no application code changed in this slice. Automated promotion and versioned release acceptance remain outstanding.
