# 6 · Limits at two layers

Docker [production settings](../deploy/compose.yaml) cap app memory at 512 MiB and CPU at 0.75 cores; PostgreSQL gets 256 MiB and 0.5 cores. These are ceilings, not promises that their CPU totals fit simultaneously on one core. Both have process/log bounds. App runtime is non-root, read-only, capability-free and has no Docker socket.

Application budgets control requests/day, reservation units/day, concurrent generations and maximum output. Role defaults can be overridden per user; admins can disable the configured model by role. Admission uses database locks so multiple workers cannot independently approve the same capacity.

A reservation conservatively counts UTF-8 input bytes plus maximum output tokens. Reservations remain charged on failure/cancellation because upstream work may already be billable. Actual provider token usage is recorded separately when available. Reservation units are not dollars or exact token billing. The global concurrent-run ceiling is operator configuration.

The [host collector](../deploy/host-metrics.py) runs separately under a systemd timer. It reads host CPU/memory/disk and selected container summaries, then atomically publishes a JSON file. The app receives that directory read-only and exposes it only through admin authorization. No app-side Docker control is needed.

The dashboard distinguishes missing/stale metrics and displays aggregate usage and audit events. Thirty-second samples retain about 30 minutes of history. This is basic monitoring, not an external uptime/alerting service. Existing Traefik/calculator behavior stays independent.

**Exercise:** lower a user's daily request limit, exhaust it, and check that restarting the app does not reset it. Then stop the collector and observe stale metrics rather than a misleading green status.
