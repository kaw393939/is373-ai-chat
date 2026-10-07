# 8 · The image you tested is the image you deploy

A release can pass tests and still deploy different bytes. Rebuilding later may resolve a changed dependency, base image or build input. Our pipeline therefore treats the tested image as an artifact to preserve, publish and identify.

**Learning outcomes:** distinguish continuous integration, delivery and deployment; trace commit/image/schema/config identity; assess credentials and recovery boundaries; identify evidence missing from a successful workflow. Read [testing](07-testing.md) and [migrations](03-data.md).

## How release work changed

Late integration and manual release batches defer feedback until many changes interact. Fowler describes continuous integration as a team practice of frequent integration and verification, not merely the presence of a CI server. Humble and Farley's 2010 *Continuous Delivery* connects build/test/deployment pipelines to the ability to keep software deployable. Automatically releasing every accepted change is a further policy choice. [Fowler](references.md#ref-ci); [Humble and Farley](references.md#ref-delivery).

This project currently verifies main and deploys directly to production. Public QA exists, but a QA hostname does not establish a promotion gate. That distinction is an opportunity to evaluate delivery policy rather than redefine completed infrastructure as a completed process.

## Worked case: one source, two possible images

Consider a synthetic commit X. Image A passes browser tests. If publication rebuilds X into image B, the source SHA may match while the image digest differs. A commit identifies source history; a digest identifies image content. Our workflow builds once, browser-tests and scans that image, saves it, then loads the saved artifact for publication. The source-commit label is checked, and deployment uses the published digest.

A release also includes configuration and schema. Identical image bytes with a different JWT key or provider attachment have different effects. The public readiness response verifies database access and reports commit/schema/provider; it does not attest to every private setting or user journey. Preserve a sanitized release record without leaking configuration secrets.

## Read the implementation

| File/symbol | Boundary to follow |
|---|---|
| [`verify`, `publish`, `deploy`](../.github/workflows/delivery.yml) | Where is the one tested artifact passed between jobs? |
| [Dockerfile](../Dockerfile) | Which build stages leave the runtime, and how is source identity labeled? |
| [Forced-command wrapper](../deploy/chat-ssh) | Which command and arguments can the deployment key request? |
| [`run` and deployment flow](../deploy/chat-deploy) | Where are label, schema and readiness checked? |
| [Release evidence](../docs/implementation-evidence.md) | Which checks ran, and which remain outstanding? |

Pull requests have read-only permissions and no deployment credentials. Main pushes publish to GitHub Container Registry (GHCR); manual runs verify without publishing. Production jobs serialize rather than cancel an active migration. GitHub uses repository secrets `DEPLOY_SSH_KEY`/`DEPLOY_KNOWN_HOSTS`, variables `DEPLOY_HOST`/`APP_URL`, and short-lived job-scoped registry tokens. Database, JWT and provider secrets stay in protected host configuration. Available GitHub environment protections depend on plan and repository visibility; none should be claimed without verification.

The root-owned deployment wrapper accepts only this repository's digest and a source SHA. Under a host lock it checks the image label, extracts the image's Compose model, validates configuration, starts/checks PostgreSQL, dumps before migration, migrates, seeds defaults and verifies the app. Its automatic previous-image recovery is limited to unchanged schema. The candidate model is now staged in a private temporary directory and validated before replacing active Compose. Database startup and protected nonempty backup creation are inside failure handling; fake-subprocess tests inject each setup failure. Changed/unknown schemas stop the app for operator recovery rather than auto-downgrade. [#13](https://github.com/kaw393939/is373-ai-chat/issues/13) still requires a controlled non-production rehearsal before closure.

## Alternatives, evidence and limits

A tag is convenient navigation but can move; deployment by digest preserves artifact identity. An SBOM lists components, while a vulnerability report evaluates known advisories at scan time. Neither guarantees future safety. The scan caught vulnerable libraries vendored in pip; removing the unused runtime installer reduced code rather than suppressing findings.

Current CI retains the tested image artifact for two days and test evidence for seven days. A historical run URL can outlive its downloadable evidence. Classroom editions therefore need archived sanitized verification records; the workflow alone is not a textbook archive. [#22](https://github.com/kaw393939/is373-ai-chat/issues/22) tracks supply-chain/evidence maintenance.

**Laboratory:** [Lab 08 — image delivery](labs/08-image-delivery.md), followed by [Lab 09 — environment promotion](labs/09-environment-promotion.md). **Evaluate:** trace one release through source SHA, image digest, schema and observed behavior, then state why an old image might be unsafe after a migration. Automated QA promotion and semantic releases remain [#24](https://github.com/kaw393939/is373-ai-chat/issues/24)/[#25](https://github.com/kaw393939/is373-ai-chat/issues/25).
