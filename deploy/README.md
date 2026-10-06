# Operator bootstrap

Read the [hosting lesson](../book/09-hosting.md) first. Run these steps as an authorized operator; use your own hostname/secrets. No private deployment key belongs on the server. The public key must be available before GitHub deployment.

```sh
sudo install -d -m 700 /opt/is373-ai-chat
sudo install -d -m 755 /var/lib/chat-metrics
sudo install -m 755 deploy/chat-deploy /usr/local/sbin/chat-deploy
sudo install -m 755 deploy/chat-ssh /usr/local/lib/chat-ssh
sudo install -m 755 deploy/host-metrics.py /usr/local/lib/chat-host-metrics.py
sudo install -m 755 deploy/backup.sh /usr/local/lib/chat-backup.sh
sudo install -m 644 deploy/chat-metrics.service deploy/chat-metrics.timer deploy/chat-backup.service deploy/chat-backup.timer /etc/systemd/system/
```

Create `/etc/sudoers.d/chat-deploy` with mode 0440 and validate with visudo:

```text
kwilliams ALL=(root) NOPASSWD: /usr/local/sbin/chat-deploy
```

Append your deployment public key to the operator's authorized_keys using this prefix, preserving existing access:

```text
restrict,command="/usr/local/lib/chat-ssh" ssh-ed25519 YOUR_PUBLIC_KEY chat-deployment
```

Create protected production .env from the example, changing APP_ENV, BASE_URL, hostname, random secrets and provider values. Set chmod 0600. Create GitHub repository secrets/variables named in Lesson 8. The forced-command wrapper accepts only `deploy sha256:DIGEST FULL_COMMIT`; GitHub sends the ephemeral registry token on stdin. The image includes versioned production Compose and migrations.

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

Host-specific account name, repository namespace and image registry are explicit in the wrapper/workflow. Adapt them together for another installation. Daily backups are local until an off-host destination is configured. Container resource settings are conservative starting ceilings, not a load-tested capacity guarantee.
