# 9 · A hostname is not a deployment

Adding `qa.example.org` to DNS only tells a client where to look. It does not create a database, configure an HTTP router, issue a certificate or deploy an app. This chapter separates those responsibilities so a learner can explain a complete installation rather than copy a hostname change.

**Learning outcomes:** trace DNS → TLS/proxy → container → database; distinguish a fresh host from an existing shared host; explain preview isolation and remaining shared risks; propose verification for each layer. Read [local configuration](02-local.md) and [delivery](08-delivery.md).

## Names, machines and packaged processes

Paul Mockapetris's 1987 RFC 1034 describes the domain-name system's concepts. Names and records provide a distributed naming mechanism; they do not specify what software must run at an address. Our case has three names resolving to one host, with Traefik selecting an application by its Host rule. [RFC 1034](references.md#ref-dns).

Containers address a different problem: repeatable process packaging. Docker's 2013 release built on existing Linux isolation primitives; it did not invent operating-system isolation or turn a container into a separate machine. Direct host installation and virtual machines remain alternatives. Packaging reduces one source of drift while networks, volumes, configuration and the host kernel remain operating responsibilities. [Container history](12-history.md#from-configured-machines-to-packaged-processes); [Docker](references.md#ref-docker).

## Worked case: three names on one host

The observed project runs dev, QA and production on the same DigitalOcean host. Each preview has a distinct Compose project, private database network, volume, JWT key and database password. Unique Traefik router/service names prevent a preview's labels from replacing production routing. Mock LLMs, disabled email and empty provider keys constrain effects; public previews still use production HTTPS/Secure-cookie enforcement.

This is useful isolation of application data and configuration, not independent infrastructure. All environments share host memory, CPU, kernel, disk and external proxy. A host outage affects them together, and resource limits are not a sustained-load acceptance test. The environment's purpose (“QA”) is separate from the application's security mode (`APP_ENV=production`). See the dated [environment runbook](../docs/environments.md) rather than treating this snapshot as permanently current.

## Two installation paths

For a fresh Ubuntu 24.04 droplet, [observed-host recreation](../docs/recreate-observed-host.md) explains the earlier SSH, firewall, Docker, DNS and Traefik arrangement. It is an observed-system reconstruction, not proof of a completed independent fresh-host rehearsal. [#7](https://github.com/kaw393939/is373-ai-chat/issues/7) owns that verification.

On the existing classroom host, the app reuses `/opt/webserver` and Docker network `web` while owning a separate project. It publishes no app/database host ports. Priority-100 Host rules select the chat; the old Apache teaching content and unrelated calculator remain separately routed. This overlap must be inspected when adapting another host, not assumed from the sample IP.

Authorized operators install the root-owned fixed deployment wrappers and policy module, validate the limited sudoers entry and configure three distinct SSH public keys scoped to dev, QA and production. Host fingerprints must be confirmed through a trusted channel; disabling SSH verification would weaken the boundary. Protected `.env` files provide private credentials, and admin bootstrap prompts for a private password rather than installing a default. The privileged wrapper fixes directory/image scope, uses a private shared host lock, and rechecks QA evidence before production promotion. Install policy and wrappers together before enabling the workflow. Collector setup also installs its sanitized backup-status companion; follow the [backup runbook](../docs/operations/backups.md) to verify recovery and off-host freshness separately.

## Read and verify each layer

| File/evidence | Question |
|---|---|
| [DNS audit](../docs/audit/2026-10-06-dns.md) | Which records changed, and which mail records were preserved? |
| [Preview Compose](../deploy/compose.preview.yaml) | What makes projects, routes, volumes and effects distinct? |
| [Operator bootstrap](../deploy/README.md) | Which host-specific paths/accounts must be adapted together? |
| [Settings](../app/config.py) | Which unsafe production values fail startup? |
| [Environment runbook](../docs/environments.md) | What did HTTPS/browser/isolation checks establish on the recorded date? |

A DNS answer, verified HTTPS response, migrated schema, login journey and cross-environment rejection establish different facts. Account-side firewall, alerting and backup settings still require their own proof. Installing the metrics collector and backup timer is also separate from merely starting the app image.

Process behavior needs a separate experiment. The [two-replica fault harness](../tests/process/README.md) runs only on disposable loopback PostgreSQL and fixed test ports. It races admission across real processes, sends SIGTERM during a stream, waits for the actual lease after KILL, and restarts mail after synthetic acceptance before its database commit. A clean exit once concealed an unsaved partial answer; explicit generator closure and finalizer joining repaired it. Read the recorded timings and durable state, and distinguish source debugging from the CI experiment on the exact release image.

**Laboratory:** [Lab 09 — environment promotion](labs/09-environment-promotion.md); shared dev/QA are observation/acceptance environments, not learner failure targets. **Evaluate:** compare the current low-cost topology with separate QA infrastructure using cost, data, failure and recovery criteria. No high-availability or zero-downtime claim is made.
