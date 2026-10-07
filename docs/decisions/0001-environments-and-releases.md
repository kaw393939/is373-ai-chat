# ADR 0001: Environment isolation and versioned promotion

Status: Accepted October 6, 2026. Shared-host previews are installed. Version/promotion code is being implemented; remote workflow/release evidence is required before claiming activation.

Implementation: [environment promotion #24](https://github.com/kaw393939/is373-ai-chat/issues/24) and [semantic releases #25](https://github.com/kaw393939/is373-ai-chat/issues/25).

## Context

The legacy CI deployed main directly to production after image tests. Installed releases have commit/digest/schema identity and legacy package metadata 1.0.0, but no historical v1.0.0 Git tag or GitHub Release was found. The owner approved persistent dev/QA previews and a public repository with protected production promotion.

## Decision

| Environment | Purpose | Isolation |
|---|---|---|
| Local | Compose/source reload | Disposable database, mock LLM/email and local secrets |
| Development | Public preview at dev.firehose360.com | Own database, volume, JWT/database secrets and Docker project; mock LLM and disabled email |
| QA | Persistent validation at qa.firehose360.com | Own hostname, database, volumes, network/project, secrets and synthetic accounts; external email/payment-like effects disabled or restricted |
| Production | Real users at firehose360.com | Protected config/data and an explicitly selected tested digest |

Use short-lived branches and one main integration line, rather than maintaining long-lived dev/qa/prod branches. A commit does not automatically mean a production release. Build once with the intended release version and source identity, test the digest in QA, then promote that digest to production without rebuilding or changing image contents. Label the environment separately from the application version.

Keep local development available. The owner selected public dev and QA hostnames. Initial installation uses the existing 1-vCPU/2-GiB host, with each preview capped at 256 MiB for the app and 128 MiB for PostgreSQL. The pre-install snapshot had about 1.1 GiB available memory and 43 GiB free disk. This is a low-traffic starting point, not a load-test capacity claim. Separate projects, private database networks, volumes and credentials isolate application data; the shared ingress network, kernel, CPU and host failure remain common. Prefer a separate QA host when an approved budget allows it. No new paid host is authorized. See the [environment runbook](../environments.md) and [DNS audit](../audit/2026-10-06-dns.md).

Use GitHub environments `development`, `qa`, and `production` for scoped keys, host configuration and deployment history. The repository is public; GitHub supports required reviewers for production in this topology. The owner must configure the reviewer before enabling promotion. A manually dispatched promotion and its reviewer gate are separate controls: dispatch selects the candidate, approval authorizes its use. Host-side verification additionally requires an accepted QA record and a completed successful main delivery run. Preview deploys and production promotion serialize without cancelling migrations.

## Version contract

Adopt MAJOR.MINOR.PATCH for the supported contracts below: breaking change / compatible feature / compatible fix. A styling change does not automatically become a major release; a database migration is reviewed for compatibility independently of its Alembic revision. Internal refactoring is not a public contract change.

| Contract | Supported boundary | Compatibility rule |
|---|---|---|
| HTTP API | Documented `/api` routes, authorization/status semantics, JSON field meanings, SSE `started`/`delta`/`error`/`completed` events | Additive optional fields and opt-in pagination are compatible; mandatory new login challenges, removals or changed meanings require a major version |
| Operator CLI | Documented `python -m app.cli` subcommands/options and exit success/failure | Removing an option, changing a required input or reversing an operation's meaning breaks the contract; human-readable prose is not a parsing API |
| Runtime configuration | Names, validation and semantics documented in environment examples/runbooks | Existing valid production configuration must remain valid for a compatible release; a required new setting or changed security policy requires explicit migration |
| Provider extension | The typed provider protocol and documented token/terminal/cancellation semantics | A replacement adapter must honor the contract; adding a required method or changing stream event meaning breaks extension compatibility |
| Deployment protocol | Fixed scoped `deploy`, `attest`, `promote` commands and JSON release records | This release requires an operator wrapper upgrade before application deployment; arbitrary shell access is outside the contract |

The first formal application release is **2.0.0**. Its required MFA encryption setting, typed provider extension and scoped deployment protocol change legacy operator/extension contracts. Enabling administrator MFA also changes the login client's contract; the matching frontend ships in the same artifact, while production enforcement waits for owner enrollment and recovery custody. The migration from untagged legacy 1.0.0 is stated explicitly; no v1.0.0 history is fabricated. Read the release's migration/recovery notes before applying it. Additional pagination remains opt-in so callers expecting arrays can continue using the legacy request form.

[`VERSION`](../../VERSION) is the authoritative application version. The image embeds it at `/app/VERSION`, its OCI label must equal it, and app health/release records derive it. Package metadata is packaging information, not a second runtime release authority. A release record maps version → source commit → immutable digest → schema → QA evidence → production deployment. GitHub Releases attach the manifest, scan/SBOM and QA evidence and link issues, atomic commits, migrations/recovery notes and canonical lessons. Tags are never moved to replace released contents; a used version is rejected even if someone removes its tag.

A prerelease such as `2.1.0-rc.1` is a distinct immutable release and receives GitHub's prerelease flag. Assign the version before building. An RC is not relabelled as stable: changing `VERSION` creates new bytes and requires new image/QA acceptance. This project accepts canonical SemVer without `+build` suffixes because commit/digest already identify build metadata. A release version cannot be reused for a different artifact, and a failed post-deployment release-publication step requires deliberate reconciliation rather than a second deployment under the same version.

## Consequences and alternatives

QA adds configuration, host/resource cost and maintenance but provides a place to reproduce failures without touching users. One host for all environments is cheaper but shares resource/failure risks. Direct automatic main-to-production is simpler but provides no persistent QA acceptance stage. SemVer improves communication only after supported interfaces are defined; commit/digest identity remains authoritative for exact recovery.

Proof is required: cross-environment isolation, failed QA blocking promotion, identical QA/prod digest, migration safety, authorized promotion and documented rollback limits. Deployment and release issues own these acceptance criteria; this ADR owns the architectural tradeoff.

Sources: [Semantic Versioning 2.0.0](https://semver.org/), [GitHub deployment environments and plan restrictions](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).
