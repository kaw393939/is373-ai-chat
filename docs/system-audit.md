# System and Docker audit — October 6, 2026

The authorized server was inspected over SSH with sudo. This audit did not install packages, restart services, modify accounts/firewalls/DNS, or change containers. Sudo authentication and normal SSH logging occurred. Credentials are excluded from project files.

The audit establishes current state and available historical evidence. It cannot prove every command ever executed, recover deleted history, or inspect DigitalOcean control-plane settings without account access. This is a configuration/operations audit, not a forensic compromise investigation or vulnerability scan.

## Evidence and reusable material

- [Curated host snapshot](audit/2026-10-06-host-snapshot.json): effective SSH settings, package inventory, services/timers, firewall and Docker NAT rules, container settings, image identities, networks, volumes, Compose models, file permissions/hashes, and certificate domain metadata.
- [Operations snapshot](audit/2026-10-06-operations-snapshot.json): Fail2Ban, update schedules/policy, routing, public deployment files, and package-history events.
- [Public endpoint checks](audit/2026-10-06-public-endpoints.json): DNS, trusted TLS, certificate expiration, and HTTP results.
- [Recreation guide](recreate-observed-host.md) and [observed files](../examples/observed-host/README.md).
- [Repeatable inspection script](../scripts/audit-host.py): intended for this known host. Review before running on another host because command/config fields outside the environment-value allowlist may contain sensitive values on other systems.

These files contain infrastructure names/paths and public SSH fingerprints. The repository remains private. Snapshot environment entries contain names and explicitly allowlisted non-secret values, rather than raw container environments. Certificate private keys, password hashes, credentials, logs, and raw shell history are not included.

## Host and administrative access

Ubuntu 24.04.5 LTS, kernel 6.8.0-142-generic, one CPU, about 1.9 GiB RAM, no swap, and about 44 GB free on a 48 GB root disk. Last recorded boot was September 29. Host timezone is UTC with active clock synchronization.

`kwilliams` is the normal interactive user and has password-protected unrestricted sudo. The Docker group is empty; Docker is operated through sudo. Root and kwilliams have the same authorized public RSA key fingerprint, but effective SSH policy disables root login. No private SSH keys were found in the two inspected .ssh directories.

Effective SSH: port 22; public-key authentication enabled; password and keyboard-interactive authentication disabled; root login disabled; TCP forwarding and X11 forwarding enabled. The main sshd_config contains `PermitRootLogin yes`, overridden by the early `00-disable-root.conf` snippet. A faithful recreation must account for OpenSSH precedence, not copy the misleading main-file line. See [Ubuntu OpenSSH configuration](https://ubuntu.com/server/docs/how-to/security/openssh-server/).

UFW is active with default incoming deny and explicit SSH/80/443 allowances for IPv4/IPv6. Docker manages separate bridge/NAT rules, captured in the snapshot. No TCP Docker API listener was observed. Host routes include public eth0, private addresses on eth0/eth1, and Docker bridges. IPv6 routes showed link-local connectivity without a default route at inspection; IPv6 firewall allowances alone do not prove public IPv6 reachability.

Fail2Ban is running with one `sshd` jail: maxretry 3, findtime 600 seconds, bantime 86400 seconds. It reported 16 current bans and 50 total bans at inspection. This is supporting evidence of an internet-facing SSH service, not proof of compromise.

## Operating system maintenance

Docker/containerd, SSH, Fail2Ban, cron, unattended-upgrades, DigitalOcean droplet-agent, logging, time synchronization, and standard Ubuntu cloud services were active. No failed systemd units were reported. No custom application startup unit or application cron job appeared in inspected inventories; Docker restart policies provide service restart behavior.

APT update-list job runs daily at **1:45 AM Eastern**, upgrade job at **2:00 AM Eastern**. Timer overrides specify `America/New_York`, zero random delay, and `Persistent=false`, so missed runs are not automatically caught up through timer persistence. Allowed unattended-upgrade origins include Ubuntu release/security and ESM origins; the Docker third-party repository is not in that allowlist. Automatic reboot is explicitly false. No reboot-required flag was present.

Cached APT metadata listed pending Docker 29.8.2, Compose 5.6.0, kernel-family packages and sosreport updates. The audit did not refresh package metadata or install them. Latest available package status can differ from this cached snapshot.

Package histories support this partial timeline, expressed in Eastern time:

| Date/time | Recorded event |
|---|---|
| Sep 29, 1:18 PM | apt-transport-https installed |
| Sep 29, 1:19 PM | DigitalOcean droplet-agent/keyring installed |
| Sep 29, 2:01 PM | apache2-utils installed |
| Sep 29, 2:02 PM | Docker CE, CLI, containerd, Buildx and Compose installed |
| Sep 29, 3:29 PM | make installed; application directory/config/state created around this period |
| Oct 1, 1:21 PM | Fail2Ban and dependencies installed |
| Oct 1, 1:23 PM | APT timer override directories modified |
| Oct 1, 2:06 PM | Current calculator image build time |

APT event timestamps are evidence of package transactions; file modification times indicate changes, not who made them. Full shell histories were deliberately not copied because they can contain credentials and incomplete commands.

## Docker topology and runtime

Docker Engine 29.8.1, Compose v5.5.1, Buildx 0.37.1, containerd.io 2.3.6. Docker uses its packaged systemd service and Unix socket. No `/etc/docker/daemon.json` was present. Two Compose projects are running:

| Project | Files | Services |
|---|---|---|
| public-web | /opt/webserver/compose.yaml | Traefik + five Apache sites |
| is373-ci-cd | /opt/is373_ci_cd/compose.yaml and compose.override.yaml | Calculator production + WUD |

All eight containers use `restart: unless-stopped`; none is privileged or has a memory/CPU limit. The development service exists in Compose but is not running. Current networks: standard bridge/host/none, shared bridge `web` on 172.18.0.0/16, and application bridge `is373-ci-cd_default` on 172.19.0.0/16. Subnets can change during recreation and need not be copied.

Traefik and the five Apache sites use `web`. Calculator production joins both `web` and its application network. WUD joins the application network only. Traefik publishes 80/443 publicly. Calculator publishes 8090 and WUD 8091 only on 127.0.0.1. No database, Redis, local LLM, or other application container is deployed.

Calculator production runs as UID/GID 10001, read-only root, all capabilities dropped, no-new-privileges, pids limit 128, and a bounded 64 MiB /tmp tmpfs. It has no bind mounts or Docker socket. Traefik and Apache have no-new-privileges but writable container roots and no explicit user override. WUD has a writable root and Docker socket with no comparable capability restrictions. Empty Config.User means the image default applies; it does not establish the effective user of every subprocess.

**Logging gap:** Traefik and all Apache services have json-file rotation at 10 MB × 3 files. Calculator and WUD use json-file with empty options, and there is no daemon-level override. Their logs are unbounded by that driver configuration. The existing hosting README's claim of all-container rotation is therefore broader than the live evidence. [Docker logging documentation](https://docs.docker.com/engine/logging/drivers/json-file/) confirms the default unlimited max-size and that logging changes require container recreation.

**Privileged boundary:** WUD mounts the Docker socket read/write, and Traefik mounts it read-only. A read-only filesystem socket mount does not restrict API calls. Keep app containers away from that socket and evaluate reducing proxy/controller access. See [Docker daemon access protection](https://docs.docker.com/engine/security/protect-access/).

## Persistent state, routing, and recovery

Five Apache document roots are read-only mounts from `/opt/webserver/sites/<hostname>`. The captured welcome pages are included in the examples. The current app is stateless and has no database storage.

Traefik stores ACME account/certificate private material in `/opt/webserver/letsencrypt/acme.json`, root-owned mode 0600. There is also `acme.before-email-change.json`; both files require private backup handling. The `dashboard.htpasswd` file is mounted, and a `dashboard-login.txt` exists, but no authentication middleware is attached to the dashboard router. File existence is not proof that authentication is enabled.

All seven configured hostnames resolved to the droplet and returned HTTP 200 over trusted TLS 1.3. Certificates expire December 28, 2026, according to observed peer metadata. Renewal is configured but no renewal exercise was performed. DNS provider records, wildcard/catch-all settings, and DigitalOcean cloud firewall/backup settings remain unverified externally.

One named volume exists: `is373-ci-cd_wud-data`, mounted at /store. It stores updater state. `/opt/is373_ci_cd/.state/wud.env` and .env are root-owned mode 0600. Only credential names were retained. No root/user Docker registry auth config was found at standard paths; existing public images do not require a private pull credential.

Both application and hosting tracked checkouts are clean and match recorded upstream commits. The locally ignored application .env sets APP_HOST=calc.mywebclass.org and TRAEFIK_NETWORK=web. Its local Compose override supplies the calculator's public route.

WUD watches only opted-in calculator production, polls once per minute, and updates from Docker Hub's prod channel. GitHub does the image testing/publication; the server pulls it without a GitHub-to-server SSH deployment key. Runtime wrapper commands manage update pause, release selection, deployment verification and rollback. A GitHub repository clone alone omits the local routing, secrets, updater state, certificates and site content needed to recreate this host.

Image identities are saved in the snapshot and pinned hosting overlay. Calculator's running image and host-reported RepoDigest are `sha256:aec414c990a5de6ed74c9e8dcb105b78f6358c03a8cea70a9d40dcda51c3a8fa`. These are host-observed identities; registry pullability on a new host has not been tested. Public /health reports source commit 4600202bad42da0c5ffb11d83ce8364671293d3d.

## Discussion before the new chat app

Prioritize bounded logs, dashboard protection, off-host backups with restoration evidence, and resource budgets. Decide how to maintain third-party Docker packages and apply kernel updates. Preserve the current key-only SSH and tested-image discipline.

For PostgreSQL/Alembic chat releases, use coordinated schema migration and application readiness checks. Keep the existing calculator's WUD behavior independent; do not automatically add the chat database/application to WUD. Current single-server capacity and Docker privilege choices should be explicit teaching decisions, not copied as production defaults.

No application backup job was found in the inspected timer/cron inventories. DigitalOcean backups, cloud firewall, monitoring/alerts and provider DNS must still be checked in their control planes. A running droplet-agent does not establish that metrics alerts or backups are enabled. No replacement droplet or restore/reboot rehearsal was performed.
