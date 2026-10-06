# Observed classroom deployment

Captured October 6, 2026 from the authorized host. These examples reproduce the existing hosting/calculator layout and are independent of the proposed AI chat implementation.

- `webserver/compose.yaml`: actual readable proxy/site definition, including the current unauthenticated dashboard.
- `webserver/compose.pinned.json`: optional amd64 image digest overrides based on the audit, for repeatable image selection.
- `webserver/sites/`: actual public welcome pages.
- `calculator/compose.override.yaml`: actual ignored server routing overlay.
- `calculator/.env.example`: observed non-secret host/network settings.
- `host-config/`: observed SSH snippets and update timer settings. The Fail2Ban file is an equivalent proposed configuration derived from effective policy, rather than a copied source file.

These are archived examples, not a recommendation to expose an unauthenticated dashboard on a new long-lived deployment. All hostnames and the ACME email must be adapted for another installation. Certificates, private keys, passwords, updater credentials/state, and registry credentials are intentionally absent. Do not start this stack on the existing server alongside its active stack.

Follow the [recreation guide](../../docs/recreate-observed-host.md). Syntax/static checks do not establish successful installation on a clean replacement droplet.
