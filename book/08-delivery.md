# 8 · The image you tested is the image you deploy

[GitHub Actions](../.github/workflows/delivery.yml) runs lint/format, unit/integration coverage, migration drift checks and a Docker build. It browser-tests that image under production-like restrictions, scans it and saves its image archive. Publication loads the saved artifact and checks its source-commit label; it never rebuilds after testing.

Pull requests have read-only permissions and no deployment credentials. Only main pushes publish to GHCR. Production jobs are serialized without cancelling a migration in progress. The workflow supports manual verification but manual runs do not publish/deploy.

Repository secret names: DEPLOY_SSH_KEY and DEPLOY_KNOWN_HOSTS. Variables: DEPLOY_HOST and APP_URL. Publishing uses the short-lived GITHUB_TOKEN with job-scoped package permissions. Provider/database/JWT keys stay in protected host configuration. Environment protections may depend on GitHub plan; this deployment uses repository secrets rather than claiming an unavailable approval gate.

The dedicated SSH key uses a forced command with forwarding disabled. A root-owned wrapper accepts only this repository's digest and a full source SHA. It obtains a short-lived registry token on stdin, uses a temporary Docker credential directory, pulls the image, checks its commit label, and extracts that image's versioned Compose model.

Under a host lock, deployment starts/checks PostgreSQL, saves a pre-migration dump, migrates once, seeds role defaults, starts the app and verifies readiness/commit. GitHub then checks the public HTTPS commit. No WUD watcher independently replaces the chat app.

Automatic app recovery restores the previous image/config only when the schema revision did not change. Otherwise deployment fails visibly and preserves a dump for an operator decision. No destructive automatic schema downgrade is attempted.

**Exercise:** trace one release through workflow URL, Git SHA, registry digest, schema revision and public health. Explain why a successful push to a registry is insufficient evidence of deployment.
