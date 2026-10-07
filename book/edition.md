# Edition and reproducibility

This is development edition **0.3.0**, prepared October 6, 2026. It is a complete
authored course path undergoing technical checks, not a classroom-validated
textbook. The [human pilot record](instructor/pilot-record.md) defines the
remaining learner evidence. The date of a test run belongs to its evidence;
authorship does not imply successful execution on every platform.

## Fixed identities

| Item | Identity / interpretation |
|---|---|
| Reviewed manuscript | `34c740cfdf8294930beadf60d0b043586cffdf78`; original review findings remain dated |
| Initial case-study app source (historical) | `d65a19c8d3cd344d31b8f01103fe5e3137a8485d`; later book/test changes are not that deployed source |
| Initial case-study image (historical) | `ghcr.io/kaw393939/is373-ai-chat@sha256:9bed602fcea38a5cc0a613e8440ce2b4663cbc6838e89c93411112e41edc4997` |
| Guarded revision image | `sha256:1d2a4fa2671d9e0f57ad1f314d03d7aaa15ebdde17df283d5aee4d45a5b66a0b`, source `d8d11a71db3779b00463eb36c9cd6d2118d1989c`; exact image browser-tested and deployed in run 37550580435 |
| Prior manuscript source | `book-v0.2.0`, recorded commit `ece094a2428aa322eeaa5bd81aa1cba17ed4af40`; its archived edition remains unchanged |
| Current manuscript source | `book-v0.3.0` is published only after this revision's book checks pass; each build records its actual source commit and whether the checkout was dirty |
| Current application contract | [`VERSION`](../VERSION) declares 2.0.0; migration head is `0003`. A declared version is separate from accepted CI and production deployment evidence |
| Built content fingerprint | `artifacts/book-build.json` records SHA-256 over the ordered book paths and contents; included in the edition bundle |
| Python/dependency/build locks | Python 3.14.7; `uv.lock`; `frontend/package-lock.json`; MkDocs 1.6.1 in the optional `book` group |
| Required database semantics | PostgreSQL 17 for locking/admission; temporary SQLite provides a quick path with PostgreSQL lock cases explicitly skipped |
| Browser | Python Playwright uses its locked package and installed Chromium revision; save `uv run playwright --version` in lab evidence |
| Verified local platform | macOS arm64; Linux amd64 container checks belong to the cited CI run, not an inference from local tests |

The old image provides provenance, not a demand to connect to a running server.
Students can build the image locally. Registry access may need authentication
independently of repository visibility. Do not put registry tokens in learner
reports. Use the disposable browser harness and mock provider; public dev, QA and
production accounts are not lab targets.

## Durable evidence and updates

Sanitized verification records live in [edition evidence](evidence/2026-10-06-revision.md).
The book workflow uploads HTML plus the build identity; the delivery workflow
retains test evidence for 90 days. CI artifacts are convenient downloads, not a
permanent archive. The committed record and fixed tag preserve the findings;
an edition release attachment preserves the rendered copy and fingerprint.

Examples of provider EOF, forged/expired claims, authorization failure and
promotion failure use fixed synthetic scenarios. Current GitHub defects are
optional extensions: an issue being fixed cannot erase the lab's teaching case.
Book versions describe teaching material changes, independently of application
semantic versions and image digests. A change to expected lab behavior requires
a new minor edition; typo/link corrections can use a patch edition. Compatibility
claims must be rechecked against their exact tool/platform matrix.
