# Lab 06: inspect a journey beyond “it renders”

## Problem, objectives and preparation

A chat page looks correct in a screenshot but must also work through keyboard actions, page reload and a narrow viewport. Distinguish functional browser evidence from accessibility conformance. Bloom emphasis: **apply, analyze, evaluate**.

Complete [preflight](README.md), [testing](../07-testing.md) and Labs 02/04. Prerequisites: browser focus, accessible names, basic Python Playwright. Install the local browser:

```sh
uv run playwright install chromium
uv run python scripts/run-browser-lab.py
```

The harness creates its own temporary SQLite database, seeds synthetic credentials, starts a mock/disabled-email server on `http://127.0.0.1:9001`, checks the unique run marker, executes the [original journeys](../../tests/e2e/test_workshop.py) and [regressions](../../tests/e2e/test_regressions.py), then stops its server. It refuses a public/unmarked target before browser requests. No Docker, existing preview account or real email is needed. CI uses a separate PostgreSQL database and the release image for the same browser modules. Requirement: [REQ-QUALITY](../../docs/project/baseline.md#req-quality).

## Guided investigation and expected checkpoints

Expected for this revision: eleven browser tests pass. Read the mobile journey: it uses labeled inputs, `Control+Enter`, conversation history, an incorrect current-password rejection and a horizontal-overflow assertion. Read the registration journey: approval happens through an admin account and ordinary users do not see Administration. Identify which assertions depend on accessible roles/names.

| Evidence | What the current tests establish | Boundary |
|---|---|---|
| Original three journeys | Registration/approval, mock chat persistence, password checks, administration and mobile overflow. | Real local API, synthetic users; no real inbox or model. |
| Delayed navigation, stream and admin save | A late response cannot restore an obsolete view, user or search. | Browser-controlled delay/response fixtures. |
| Two tabs and factor replacement | Cookie rotations serialize; logout/replacement invalidates peers; one-time codes remain visible. | Real cookie/API exchanges; one controlled 401 simulates access expiry. |
| Keyboard dialogs | Rename/Delete/Edit account initial focus, boundary wrapping, Escape, focus restoration and an error's `alert` role. | Chromium keyboard assertions, not a screen-reader announcement audit. |
| Pagination, export and Markdown | Older pages remain reachable; cancelled exports cannot download; hostile HTML/image/link inputs remain inert. | Controlled large pages, export timing and display content; API ownership has separate integration tests. |

Inspect the generated screenshots in `artifacts/`. They can reveal clipping and confusing hierarchy, but cannot establish contrast, screen-reader behavior or all keyboard paths. Read the keyboard assertions beside [Dialog](../../frontend/src/Dialog.tsx), then write a checklist for those missing checks. The concrete #19 keyboard regressions are now implemented; passing them does not establish accessibility conformance.

## Fixed fault and smallest repair

The mobile fixture submits an incorrect current password. Predict the visible error and continued authenticated state; then locate the assertions proving both. This tests a failed user action rather than a successful screenshot.

For the keyboard experiment, follow trigger→dialog→first input→Shift+Tab→last button→Escape→trigger. Native `showModal()` makes background content inert, but the tested Chromium path needed an explicit boundary wrap to keep Shift+Tab from leaving document controls. In a private local branch, temporarily remove that boundary guard and predict which assertion fails. Restore it before leaving the lab. The current tests assert trigger restoration for Rename/Delete/Edit account; do not extend that claim to every app dialog or assistive technology.

## Evidence, transfer and reflection

Submit eleven-test output, one annotated screenshot, the failing/restored focus assertion and a table separating real API exchanges, controlled response fixtures and untested accessibility concerns. Explain why a mobile viewport is not equivalent to testing a physical mobile browser.

Transfer: in a private local branch, assess another dialog or an error-announcement path and add a behavior-based browser assertion where a gap exists. Compare native `<dialog>` behavior with the small boundary guard. Keep the mock provider and harness guards. Explain a tradeoff for keyboard, pointer and assistive-technology users; an `alert` role alone does not prove what a particular screen reader announces.

## Troubleshooting, cleanup and status

If Chromium is missing, repeat installation. If port 9001 is busy, identify the existing owner; the harness must not adopt an arbitrary server. Sign-in pacing respects the app's real throttle, so the suite can wait for the next minute. If a locator stops matching, inspect the accessible name before replacing it with a fragile CSS selector. The harness cleans its server/database; keep evidence screenshots. Automated evidence is linked above; human pilot, assistive-technology review and learner transfer assertions remain pending.
