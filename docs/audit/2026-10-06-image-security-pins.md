# A pinned base still needs security maintenance

Delivery [37555797486](https://github.com/kaw393939/is373-ai-chat/actions/runs/37555797486), candidate [d9439dd](https://github.com/kaw393939/is373-ai-chat/commit/d9439dd4ccadad706d34ec8de5c2f205baec2d05), failed the existing fixable HIGH/CRITICAL vulnerability gate on October 6, 2026 (America/New_York; scan at 2026-10-07 01:13 UTC). Its lint, Python coverage, migration parity, npm audit, image build and exact-image browser steps passed first. Publication, dev/QA deployment and the exact-image process experiment did not run. This candidate was not released or deployed.

The scan identified seven fixable HIGH package/CVE pairs, representing three distinct CVEs:

| Runtime package | Installed → selected vendor fix | CVE / primary evidence |
|---|---|---|
| `libpcre2-8-0` | `10.46-1~deb13u2` → `10.46-1~deb13u3` | [CVE-2026-103111](https://security-tracker.debian.org/tracker/CVE-2026-103111) |
| `libssl3t64`, `openssl`, `openssl-provider-legacy` | `3.5.7-1~deb13u2` → `3.5.7-1~deb13u3` | [CVE-2026-75804](https://security-tracker.debian.org/tracker/CVE-2026-75804), [CVE-2026-84782](https://security-tracker.debian.org/tracker/CVE-2026-84782); [Debian DSA-6531-1](https://security-tracker.debian.org/tracker/DSA-6531-1) |

The official Docker registry still resolved `python:3.14.7-slim-trixie` to the existing pinned index `sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d`. The moving `3.14-slim-trixie` tag selected Python 3.14.8, a broader tool change. The minimal repair retains the 3.14.7 base and installs exactly the four vendor-fixed package versions in the runtime stage. Debian's [signed security repository](https://deb.debian.org/debian-security/dists/trixie-security/InRelease) supplies package authentication; its amd64 package index confirms these versions are available. The failed [sanitized scan summary](2026-10-06-image-security-pins.json) records the selection.

This is a locked package selection, not a bit-for-bit reproducible source build or a permanent archive. A rolling repository can withdraw an old version; the build must fail and request a reviewed pin refresh. No floating `apt-get upgrade`, new ignore entry or relaxed gate was added. The application source and Python/tool matrix are unchanged. A fresh image must repeat the full existing CI gates, including browser, scan and two-process faults, before dev/QA acceptance and promotion of that same digest.

The failed report separately contains 44 unfixed HIGH package/CVE pairs across eight distinct CVEs, recorded in the JSON. The existing `--ignore-unfixed` gate remains unchanged; the complete report and SBOM retain those findings. A successful fixable gate does not mean zero vulnerabilities or establish exploitability in this application's configuration. No deployment success is inferred from the patch. The immutable book 0.3.0 edition retains its previously checked source and is not republished for this application image change. Traceability: [#22](https://github.com/kaw393939/is373-ai-chat/issues/22).
