# Runtime security refresh — 13 November 2026

Refresh the pinned Python runtime from 3.14.7 to 3.14.10, apply the published
Trixie zlib security revision, remove bootstrap package-manager code from the
runtime, and update dnspython to 2.9.2. Application version 2.0.2 preserves the
existing API and schema. No migration or credential change is introduced.

The live-image audit found five fixable high-severity occurrences in the prior
image. Remaining Debian advisories without a vendor fix require ongoing triage;
there is no blanket scanner exclusion. The existing exact-image vulnerability
gate, browser tests, QA smoke tests and immutable promotion process remain in use.

Local deployment/operations/safety checks: 97 passed, two integration-only cases
skipped. Full CI, exact-image scan and live deployment evidence remain required.

The first PR CI run exposed uv 0.12.15's frozen Python download list, which did not include the new patch release. Pin uv 0.13.8 in the Docker builder and both workflows, and align the book workflow with Python 3.14.10. [uv documents the frozen download list](https://docs.astral.sh/uv/concepts/python-versions/#installing-a-python-version).

The next CI run exposed a pre-existing minute-boundary test race: the login throttle test froze the services clock, while attempt accounting uses `app.throttling.now`. Freeze the actual throttle clock so the eleven requests stay in one bucket; the HTTP 429 assertion remains unchanged. Runtime rate limiting is unchanged.

Refresh the PostgreSQL 17 Alpine image in production/preview Compose and the CI database service to the same immutable vendor digest. This retains PostgreSQL major version 17 and existing volumes. The refreshed image has no high/critical findings in PostgreSQL or its OS packages in the current scan; 26 high findings remain in the embedded Go standard library of the gosu privilege-drop helper. These are tracked separately from network-serving PostgreSQL components; their presence is not evidence of exploitation. The rollout still requires consistent database backups, one environment at a time, and live health verification.
