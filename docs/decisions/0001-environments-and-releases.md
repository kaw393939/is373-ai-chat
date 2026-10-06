# ADR 0001: Environment isolation and versioned promotion

Status: Hostnames and initial shared-host topology accepted by the owner; automated promotion and version policy remain proposed. October 6, 2026.

Implementation: [environment promotion #24](https://github.com/kaw393939/is373-ai-chat/issues/24) and [semantic releases #25](https://github.com/kaw393939/is373-ai-chat/issues/25).

## Context

Current CI publishes/deploys main directly to production after image tests. The app has commit/digest/schema identity and package metadata version 1.0.0, but no Git tags or GitHub Releases were found during this review. Persistent QA, promotion and a declared compatibility/version contract are missing.

## Proposed decision

| Environment | Purpose | Isolation |
|---|---|---|
| Local | Compose/source reload | Disposable database, mock LLM/email and local secrets |
| Development | Public preview at dev.firehose360.com | Own database, volume, JWT/database secrets and Docker project; mock LLM and disabled email |
| QA | Persistent validation at qa.firehose360.com | Own hostname, database, volumes, network/project, secrets and synthetic accounts; external email/payment-like effects disabled or restricted |
| Production | Real users at firehose360.com | Protected config/data and an explicitly selected tested digest |

Use short-lived branches and one main integration line, rather than maintaining long-lived dev/qa/prod branches. A commit does not automatically mean a production release. Build once with the intended release version and source identity, test the digest in QA, then promote that digest to production without rebuilding or changing image contents. Label the environment separately from the application version.

Keep local development available. The owner selected public dev and QA hostnames. Initial installation uses the existing 1-vCPU/2-GiB host, with each preview capped at 256 MiB for the app and 128 MiB for PostgreSQL. The pre-install snapshot had about 1.1 GiB available memory and 43 GiB free disk. This is a low-traffic starting point, not a load-test capacity claim. Separate projects, private database networks, volumes and credentials isolate application data; the shared ingress network, kernel, CPU and host failure remain common. Prefer a separate QA host when an approved budget allows it. No new paid host is authorized. See the [environment runbook](../environments.md) and [DNS audit](../audit/2026-10-06-dns.md).

Use GitHub deployment environments for environment-scoped configuration and deployment history. Verify which protection features are available on this private repository's plan. If required reviewers are unavailable, implement a restricted explicit promotion workflow rather than claiming a gate exists. Parallel QA activity must not cancel production migration/promotion.

## Version contract

Adopt MAJOR.MINOR.PATCH for the declared supported HTTP API, operator CLI/configuration and provider integration contracts: breaking change / compatible feature / compatible fix. A styling change does not automatically become a major release; a database migration is reviewed for compatibility independently of its Alembic revision.

Choose one authoritative application version and derive release metadata rather than maintaining unrelated frontend/backend numbers. A release record maps version → source commit → immutable digest → schema → QA evidence → production deployment. GitHub Releases link issues, migrations, recovery notes and canonical lessons. Tags are never moved to replace released contents.

The first formal version requires an explicit decision reconciling existing 1.0.0 package metadata; do not invent a historical v1.0.0 tag or silently rewind the published application identity. A genuine pre-release may use a name such as 1.1.0-rc.1, but metadata must match the immutable artifact. Do not rebuild or rewrite an RC image merely to rename it stable; define version assignment before the build and test any new artifact again.

## Consequences and alternatives

QA adds configuration, host/resource cost and maintenance but provides a place to reproduce failures without touching users. One host for all environments is cheaper but shares resource/failure risks. Direct automatic main-to-production is simpler but provides no persistent QA acceptance stage. SemVer improves communication only after supported interfaces are defined; commit/digest identity remains authoritative for exact recovery.

Proof is required: cross-environment isolation, failed QA blocking promotion, identical QA/prod digest, migration safety, authorized promotion and documented rollback limits. Deployment and release issues own these acceptance criteria; this ADR owns the architectural tradeoff.

Sources: [Semantic Versioning 2.0.0](https://semver.org/), [GitHub deployment environments and plan restrictions](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).
