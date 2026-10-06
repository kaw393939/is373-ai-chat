# 9 · Two installation paths

For a fresh DigitalOcean Ubuntu 24.04 droplet, follow the [observed-host recreation](../docs/recreate-observed-host.md) for SSH, firewall, Docker, DNS, Traefik and HTTPS. Adapt hostnames and enable dashboard protection for a long-lived host. Do not copy private certificate state into Git.

For the existing classroom host, reuse `/opt/webserver` and Docker network `web`. The chat project is separate and publishes no application/database host ports. Its unique Host rule routes chat.mywebclass.org through the existing HTTPS entrypoint. The calculator remains independent.

An operator installs root-owned `deploy/chat-deploy` and `deploy/chat-ssh`, grants only the fixed deployment entrypoint passwordless sudo, and adds the dedicated public deployment key as a restricted forced-command authorized key. Confirm host fingerprints through an existing trusted session before creating DEPLOY_KNOWN_HOSTS. Never disable host-key checking.

Create root-owned `/opt/is373-ai-chat/.env` with mode 0600. Set production BASE_URL/APP_HOST, a random JWT_SECRET, PostgreSQL password, approval policy and provider configuration. The deployed Compose file supplies the internal DATABASE_URL. Settings validation fails startup for unsafe production values. No credentials are included in these installation files.

Install the host-metrics service/timer and read-only metrics directory. After first deployment, bootstrap an admin through a one-off app command with a private password; role defaults are seeded automatically. Enable the backup/pruning timer. For concrete commands and verification, see [server bootstrap](../deploy/README.md).

Capacity is deliberately small: one app process, bounded DB pool, four globally admitted streams and two bounded containers on the audited 2 GB host. Load-test before increasing concurrency. No zero-downtime or high-availability claim is made.

**Exercise:** install on a disposable host and record the exact steps/evidence. Only that rehearsal validates the written guide.
