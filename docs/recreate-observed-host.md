# Recreate the observed server

This guide reconstructs the audited October 6 classroom setup. It does not install the future AI chat application. The [audit](system-audit.md) documents verified state and gaps. These steps have not been rehearsed on a clean replacement droplet; do not treat them as a verified disaster-recovery procedure yet.

Use a **new Ubuntu 24.04 LTS amd64 droplet** or a controlled recovery target. The existing server already owns ports 80/443 and must not receive a second copy of this stack. An exact byte-for-byte OS recreation would need its original cloud image and retained package artifacts; the inventory records versions, while ordinary APT installs may now select newer packages.

## 1. Provision and retain access

Create the droplet and install your authorized public SSH key through DigitalOcean. Establish a normal user with sudo, install its authorized_keys with .ssh mode 0700 and file mode 0600, and verify login/sudo in another session before disabling root access. Use a newly chosen administrative password; credentials from this conversation are not installation defaults.

Install required host utilities: git, python3, make, curl, ca-certificates, apache2-utils, ufw, fail2ban, unattended-upgrades. The observed Git package existed even though it did not appear as a manually marked package. Preserve the provider's networking/cloud-init configuration rather than copying the audited IP addresses or interface subnet assignments.

Apply key-only login and no-root-login through early SSH snippets. Inspect `sudo sshd -T` and validate `sudo sshd -t` before reloading. Ubuntu may use SSH socket activation; consult its SSH guide before changing listeners. Keep the working operator session open while verifying access.

```sh
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Set corresponding DigitalOcean cloud firewall rules and document which operator IPs may use SSH. Those control-plane settings were not captured by the host audit.

Apply the effective Fail2Ban policy using the supplied proposed jail file or reviewed equivalent. Confirm `fail2ban-client status sshd`, maxretry=3, findtime=600 and bantime=86400. Existing ban lists are transient state and should not be restored blindly.

## 2. Obtain versioned source and install Docker

From an operator-owned working directory:

```sh
git clone https://github.com/kaw393939/is373-ai-chat.git
cd is373-ai-chat
git clone https://github.com/kaw393939/373_hosting.git hosting-reference
git -C hosting-reference checkout 9d828ad1cf3b72d3c6379e074474683eae0cdd8f
sudo bash hosting-reference/scripts/install-docker.sh
```

Review the installer first. It installs through Docker's official Ubuntu repository and enables Docker at boot. It selects available package versions, not the exact historical versions. Compare installed versions to the snapshot and record any intentional differences.

Do not add the operator to the Docker group merely to avoid sudo: that group provides broad host authority. No Docker TCP API should be exposed.

## 3. Restore hosting files and private state

Copy `examples/observed-host/webserver` into `/opt/webserver`, retaining the layout. Adapt domains, ACME email, and site text before starting on a different hostname. The named web bridge is declared by Compose and will be created by the hosting project; application Compose later references it as external.

Create root-owned `/opt/webserver/letsencrypt` and `/opt/webserver/secrets` directories, mode 0700. For a recovery with a private backup, securely restore acme.json with owner root:root, mode 0600. Otherwise create an empty acme.json with those permissions and let Traefik issue new certificates after DNS and ports are correct. Do not put private certificate state in Git.

The archived definition mounts `secrets/dashboard.htpasswd` even though authentication is disabled. Create the file before starting; an interactive command avoids putting its password in shell history:

```sh
sudo htpasswd -cB /opt/webserver/secrets/dashboard.htpasswd dashboard-admin
sudo chmod 600 /opt/webserver/secrets/dashboard.htpasswd
```

Generating that file does **not** activate authentication. Attach reviewed BasicAuth middleware to the dashboard router or remove public dashboard routing for a hardened deployment. The audit preserves the historical configuration for explanation.

Point each chosen hostname to the replacement IP. Existing examples use firehose360.com, www.firehose360.com, dev.firehose360.com, mywebclass.org, www.mywebclass.org, traefik.firehose360.com, and calc.mywebclass.org. Do not change live DNS during a test restoration unless intentionally performing a cutover. Use staging hostnames and Let's Encrypt staging for rehearsals where appropriate.

Validate then start, from /opt/webserver:

```sh
sudo docker compose -f compose.yaml -f compose.pinned.json config --quiet
sudo docker compose -f compose.yaml -f compose.pinned.json up -d
sudo docker compose -f compose.yaml -f compose.pinned.json ps
```

The pinned override selects the observed amd64 digests; it requires those images to remain available in their registries. Omitting it follows the historical version/moving tags but cannot guarantee the same image bytes. `docker compose config --quiet` checks configuration, not DNS/TLS or registry availability.

## 4. Recreate calculator delivery integration

```sh
sudo git clone https://github.com/kaw393939/is373_ci_cd.git /opt/is373_ci_cd
sudo git -C /opt/is373_ci_cd checkout 4600202bad42da0c5ffb11d83ce8364671293d3d
sudo install -m 644 examples/observed-host/calculator/compose.override.yaml /opt/is373_ci_cd/compose.override.yaml
sudo install -m 600 examples/observed-host/calculator/.env.example /opt/is373_ci_cd/.env
```

Adapt APP_HOST if using a recovery hostname; keep TRAEFIK_NETWORK matching the hosting network. Use the application's wrapper commands so ignored local overlays and release-state precedence remain effective.

For a deterministic recovery, prevent the updater from following a newer prod release and use the recorded digest. From /opt/is373_ci_cd:

```sh
sudo install -d -m 700 .state
sudo touch .state/updates-paused
sudo env PROD_IMAGE=kaw393939/is373_ci_cd@sha256:aec414c990a5de6ed74c9e8dcb105b78f6358c03a8cea70a9d40dcda51c3a8fa make deploy
sudo env PROD_IMAGE=kaw393939/is373_ci_cd@sha256:aec414c990a5de6ed74c9e8dcb105b78f6358c03a8cea70a9d40dcda51c3a8fa make verify-production
```

Persist the same selection with the wrapper's `make rollback RELEASE=sha256:...` command if needed; it leaves updates paused. On the audited host WUD is active, so after verifying deterministic recovery, **deliberately** use `sudo make resume-updates` only if the current prod channel is suitable. That resumes the historical polling behavior and may replace the recorded image with a newer release.

The wrapper generates ignored `.state/wud.env` credentials if absent. To retain prior credentials/updater history, restore that protected file and the named WUD volume from a private backup instead. Do not reconstruct them from a Git repo. The WUD image's observed digest is already pinned in the upstream Compose file.

## 5. Restore maintenance schedules and document policy

Copy the observed daily timer snippets into `/etc/systemd/system/apt-daily.timer.d/schedule.conf` and `/etc/systemd/system/apt-daily-upgrade.timer.d/schedule.conf`, then run daemon-reload and restart those timers. Verify schedules through `systemctl list-timers` and effective package policy through `apt-config dump`.

The observed schedules are 1:45 AM and 2:00 AM America/New_York, automatic reboot false, timer persistence false. Ubuntu security updates are enabled; Docker's third-party repository requires a separate maintenance policy. Do not infer that daily Ubuntu updates keep pinned container images or Docker packages current.

## 6. Verify reconstruction and recovery gaps

Inspect running containers, images/digests, mounts, published ports, networks, restart/security/log settings, and services. Verify the five public pages, dashboard access policy, calculator release endpoint, redirects and certificate validity. Use the repeatable audit script and compare semantic settings rather than container IDs, bridge IDs, timestamps or randomly allocated subnets.

The source layout, images and configuration can be reconstructed from this project plus versioned companion repos. The private backup inventory must separately cover ACME files, WUD credentials/volume, operator access and any future database. No certificate keys or credentials are published here.

Reboot/restart and restore exercises remain pending: do them on a disposable recovery host before claiming validated recovery. The current audit found no application backup schedule. Confirm DigitalOcean backups, cloud firewall and monitoring in the account; add off-host backups and a restore test. For the future AI chat, implement migration-aware deployment, PostgreSQL backups, bounded logs, dashboard protection and resource limits rather than inheriting every classroom setting.
