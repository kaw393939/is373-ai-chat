# 8 · The image you tested is the image you deploy

A release can pass tests and still deploy different bytes. Rebuilding later may resolve a changed dependency, base image or build input. Our pipeline therefore treats the tested image as an artifact to preserve, publish and identify.

**Learning outcomes:** distinguish continuous integration, delivery and deployment; trace commit/image/schema/config identity; assess credentials and recovery boundaries; identify evidence missing from a successful workflow. Read [testing](07-testing.md) and [migrations](03-data.md).

## How release work changed

Late integration and manual release batches defer feedback until many changes interact. Fowler describes continuous integration as a team practice of frequent integration and verification, not merely the presence of a CI server. Humble and Farley's 2010 *Continuous Delivery* connects build/test/deployment pipelines to the ability to keep software deployable. Automatically releasing every accepted change is a further policy choice. [Fowler](references.md#ref-ci); [Humble and Farley](references.md#ref-delivery).

The legacy pipeline deployed main directly to production. The new pipeline separates verification, development/QA acceptance and explicit production promotion. A QA hostname alone is insufficient: evidence must connect that environment’s observed behavior to the exact artifact selected for production. Read the dated runbook for executed promotion evidence rather than inferring it from source configuration.

## Worked case: one source, two possible images

Consider a synthetic commit X. Image A passes browser tests. If publication rebuilds X into image B, the source SHA may match while the image digest differs. A commit identifies source history; a digest identifies image content. Our workflow builds once, browser-tests and scans that image, saves it, then loads the saved artifact for publication. The source-commit label is checked, and deployment uses the published digest.

A release also includes configuration and schema. Identical image bytes with a different JWT key or provider attachment have different effects. The public readiness response verifies database access and reports version/commit/schema/provider; it does not attest to every private setting or user journey. Preserve a sanitized release record without leaking configuration secrets. `VERSION` identifies the application release; the source SHA identifies history; the image digest identifies bytes; Alembic identifies schema. These identities answer different questions.

## Read the implementation

| File/symbol | Boundary to follow |
|---|---|
| [`verify`, `publish`, `development`, `qa`, `attest`](../.github/workflows/delivery.yml) | Where is the one tested artifact passed between jobs? |
| [Manual production promotion](../.github/workflows/promote.yml) | Which completed QA run authorizes the same digest? |
| [Dockerfile](../Dockerfile) | Which build stages leave the runtime, and how is source identity labeled? |
| [Forced-command wrapper](../deploy/chat-ssh) | Which command and arguments can the deployment key request? |
| [`Runner`, `deploy` and `main`](../deploy/chat-deploy) | Where are label, schema and readiness checked? |
| [`promotion` and `verify_run`](../deploy/release_policy.py) | Why can a failed QA job or stale record not authorize production? |
| [Release evidence](../docs/implementation-evidence.md) | Which checks ran, and which remain outstanding? |

Pull requests have read-only permissions and no deployment credentials. Main pushes publish to GitHub Container Registry (GHCR), then deploy development and QA; manual delivery runs verify without publishing. QA tests ordinary synthetic login, streaming, saved history, refresh/logout and public identity with mock chat/mail disabled. Only a successful completed main delivery run plus the currently matching root-owned QA attestation can authorize production. Manual promotion and its protected environment select that digest. The sole-owner reviewer may approve their own dispatch; this establishes authenticated review, not two-person control.

Environment-scoped secrets `DEPLOY_SSH_KEY`/`DEPLOY_KNOWN_HOSTS` and variable `DEPLOY_HOST` serve distinct dev/QA/production key scopes. Short-lived job tokens provide registry/API access. Database, JWT and provider secrets stay in protected host configuration. Workflow and host locks serialize without cancelling an active migration. [The runbook](../docs/install-and-delivery.md) records configuration and operational acceptance.

The root-owned deployment wrapper accepts only fixed scoped commands, this repository's digest, a source SHA and a canonical version. Under a host lock it checks the image label, extracts the image's Compose model, validates configuration, starts/checks PostgreSQL, dumps before migration, migrates, seeds defaults and verifies the app. Its automatic previous-image recovery is limited to unchanged schema. The candidate model is now staged in a private temporary directory and validated before replacing active Compose. Database startup and protected nonempty backup creation are inside failure handling; fake-subprocess tests inject each setup failure. Changed/unknown schemas stop the app for operator recovery rather than auto-downgrade. [#13](https://github.com/kaw393939/is373-ai-chat/issues/13) still requires a controlled non-production rehearsal before closure.

## Alternatives, evidence and limits

A tag is convenient navigation but can move; deployment by digest preserves artifact identity. An SBOM lists components, while a vulnerability report evaluates known advisories at scan time. Neither guarantees future safety. The scan caught vulnerable libraries vendored in pip; removing the unused runtime installer reduced code rather than suppressing findings.

CI retains the tested image transfer artifact for two days and verification/QA evidence for 90 days. Production promotion archives candidate, scan/SBOM, deployment record and linked atomic commits as immutable GitHub Release assets. A historical run URL can outlive downloadable CI artifacts; a traceable release preserves its evidence. Node/Python/PostgreSQL build inputs and actions are pinned; reviewed dependency updates replace automatic drift. Pins still need timely security maintenance. [#22](https://github.com/kaw393939/is373-ai-chat/issues/22) tracks that process.

The first formal application release is 2.0.0, following untagged legacy 1.0.0. Enforced administrator MFA changes login compatibility and ships with the matching frontend. A prerelease is a distinct artifact; changing RC metadata to stable requires a new build/QA pass. Used/moved release identities are refused. [ADR 0001](../docs/decisions/0001-environments-and-releases.md) defines API/CLI/config/provider contracts and version rules.

**Laboratory:** [Lab 08 — image delivery](labs/08-image-delivery.md), followed by [Lab 09 — environment promotion](labs/09-environment-promotion.md). **Evaluate:** trace one release through source SHA, image digest, schema and observed behavior, then state why an old image might be unsafe after a migration. Executed QA promotion and semantic release evidence remain [#24](https://github.com/kaw393939/is373-ai-chat/issues/24)/[#25](https://github.com/kaw393939/is373-ai-chat/issues/25).
