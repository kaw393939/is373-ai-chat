# Security reporting

Report a vulnerability through [GitHub private vulnerability reporting](https://github.com/kaw393939/is373-ai-chat/security/advisories/new). Include the affected commit or image digest, a minimal reproduction using synthetic data, expected behavior and observed impact. Do not put credentials, personal records, recovery links or exploit details in public issues.

The application and its teaching material are actively developed. The current `main` branch receives fixes; release records identify the exact tested image. An old book example or an earlier deployment is not a promise that its dependencies remain supported. See the [review evidence](docs/review-and-security.md) and [open security work](https://github.com/kaw393939/is373-ai-chat/issues?q=is%3Aopen+label%3A%22area%3Asecurity%22).

Reproduce findings in the [disposable browser lab](book/labs/06-browser-accessibility.md) or your own installation. Production permission belongs to the operator: do not run destructive tests, denial-of-service probes, account enumeration or credential attacks against the public teaching host. Our test-target guards deliberately reject production addresses.

Keep runtime `.env` files, backup identities, deployment keys and private evidence out of Git. If a credential is exposed, revoke it at its provider and rotate the affected configuration; deleting the public copy alone does not invalidate it. Maintainers should acknowledge reports privately, reproduce the finding, ship a tested fix and agree on disclosure timing with the reporter.
