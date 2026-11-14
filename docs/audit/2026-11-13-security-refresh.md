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
