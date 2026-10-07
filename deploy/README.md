# Operator bootstrap

Read the [hosting lesson](../book/09-hosting.md) first. Run these steps as an authorized operator; use your own hostname/secrets. No private deployment key belongs on the server. The public key must be available before GitHub deployment.

```sh
sudo install -d -m 700 /opt/is373-ai-chat
sudo install -d -m 700 /opt/is373-ai-chat-dev /opt/is373-ai-chat-qa /var/lib/chat-release
sudo install -d -m 755 /var/lib/chat-metrics
sudo install -m 755 deploy/chat-deploy /usr/local/sbin/chat-deploy
sudo install -m 755 deploy/chat-ssh /usr/local/lib/chat-ssh
sudo install -m 644 deploy/release_policy.py /usr/local/lib/chat-release-policy.py
sudo install -m 755 deploy/host-metrics.py /usr/local/lib/chat-host-metrics.py
sudo install -m 644 deploy/backup_status.py /usr/local/lib/backup_status.py
sudo install -m 755 deploy/backup.sh /usr/local/lib/chat-backup.sh
sudo install -m 644 deploy/chat-metrics.service deploy/chat-metrics.timer deploy/chat-backup.service deploy/chat-backup.timer /etc/systemd/system/
```

Create `/etc/sudoers.d/chat-deploy` with mode 0440 and validate with visudo:

```text
kwilliams ALL=(root) NOPASSWD: /usr/local/sbin/chat-deploy
```

Append your deployment public key to the operator's authorized_keys using this prefix, preserving existing access:

```text
restrict,command="/usr/local/lib/chat-ssh dev" ssh-ed25519 DEV_PUBLIC_KEY chat-dev
restrict,command="/usr/local/lib/chat-ssh qa" ssh-ed25519 QA_PUBLIC_KEY chat-qa
restrict,command="/usr/local/lib/chat-ssh production" ssh-ed25519 PRODUCTION_PUBLIC_KEY chat-production
```

Generate three dedicated Ed25519 keypairs locally inside ignored mode-0700 `.state/deploy-keys`; keep private keys off the server. Create protected production `.env` from the example with production HTTPS/hostname, independently generated secrets and provider values. For dev/QA use [.env.preview.example](../.env.preview.example) and distinct credentials; preview Compose forces mock chat and disabled email. Set mode 0600 and root ownership; protect each root directory with mode 0700. Do not copy production secrets/data into previews. The image contains both production/preview Compose and migrations.

Configure GitHub environments `development`, `qa`, `production`, each restricted to main, with its scoped `DEPLOY_SSH_KEY`, verified `DEPLOY_KNOWN_HOSTS` and `DEPLOY_HOST` variable. Production requires the owner reviewer and disabled admin bypass; the sole-owner topology permits self-review. This is authenticated review, not independent two-person approval. Keep immutable releases enabled. Provision an approved active ordinary QA account and put its email/password in QA-only `QA_SMOKE_EMAIL`/`QA_SMOKE_PASSWORD` secrets.

Each key's forced command fixes its environment and accepts only `deploy dev|qa DIGEST SHA VERSION`, QA-only `attest DIGEST SHA VERSION RUN_ID`, or production-only `promote DIGEST SHA VERSION QA_RUN_ID`. No scope permits a shell or arbitrary deployment path. GitHub sends the ephemeral registry/API token on stdin. Full configuration/recovery is in the [delivery runbook](../docs/install-and-delivery.md); install wrappers and policy together before enabling the new workflow.

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now chat-metrics.timer
# Enable backup only after the first deployment has created its Compose/database.
sudo systemctl enable --now chat-backup.timer
```

Bootstrap admin after the first successful deployment:

```sh
cd /opt/is373-ai-chat
sudo env APP_IMAGE="$(sudo cat current-image)" docker compose run --rm -it app python -m app.cli admin --email YOUR_ADMIN_EMAIL
```

It prompts for a password of at least 16 characters. No default production credential exists. Read-only app containers receive runtime secrets as environment values; do not print full docker inspect/config output into public logs.

Host-specific account name, repository namespace and image registry are explicit in the wrapper/workflow. Adapt them together for another installation. Follow [encrypted backup/off-host setup](../docs/operations/backups.md) and verify restore/receipt freshness separately; installation alone does not prove recovery. Container resource settings are conservative starting ceilings, not a load-tested capacity guarantee.
