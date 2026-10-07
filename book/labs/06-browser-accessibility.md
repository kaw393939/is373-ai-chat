# Lab 06: inspect a journey beyond “it renders”

## Problem, objectives and preparation

A chat page looks correct in a screenshot but must also work through keyboard actions, page reload and a narrow viewport. Distinguish functional browser evidence from accessibility conformance. Bloom emphasis: **apply, analyze, evaluate**.

Complete [preflight](README.md), [testing](../07-testing.md) and Labs 02/04. Prerequisites: browser focus, accessible names, basic Python Playwright. Install the local browser:

```sh
uv run playwright install chromium
uv run python scripts/run-browser-lab.py
```

The harness creates its own temporary database, seeds synthetic credentials, starts a mock/disabled-email server on `http://127.0.0.1:9001`, checks the unique run marker, executes the three [journeys](../../tests/e2e/test_workshop.py) and stops its server. It refuses a public/unmarked target before browser requests. No existing preview account or real email is needed. Requirement: [REQ-QUALITY](../../docs/project/baseline.md#req-quality).

## Guided investigation and expected checkpoints

Expected: three browser tests pass. Read the mobile journey: it uses labeled inputs, `Control+Enter`, conversation history, an incorrect current-password rejection and a horizontal-overflow assertion. Read the registration journey: approval happens through an admin account and ordinary users do not see Administration. Identify which assertions depend on accessible roles/names.

Inspect the generated screenshots in `artifacts/`. They can reveal clipping and confusing hierarchy, but cannot establish keyboard order, announced errors, contrast or screen-reader behavior. Write a checklist for those missing checks. Identify initial focus, tab order, Escape behavior and focus restoration for a dialog. Existing dialog accessibility work remains #19; do not infer conformance from the three passing journeys.

## Fixed fault and smallest repair

The mobile fixture submits an incorrect current password. Predict the visible error and continued authenticated state; then locate the assertions proving both. This tests a failed user action rather than a successful screenshot. For an accessibility fault, use this fixed review scenario: a modal closes but focus disappears to the document body. Write the expected trigger→dialog→close→trigger focus sequence and the Playwright assertion that would detect the failure. The scenario is an assessment fixture; do not claim that its proposed assertion has already run against every app dialog.

## Evidence, transfer and reflection

Submit three-test output, one annotated screenshot, the focus sequence and a table separating tested journeys from untested accessibility concerns. Explain why a mobile viewport is not equivalent to testing a physical mobile browser.

Transfer: in a private local branch, improve one dialog's focus management or error announcement and add a behavior-based browser assertion. Compare native `<dialog>` behavior with custom focus management. Keep the mock provider and harness guards. Explain a tradeoff for keyboard, pointer and assistive-technology users.

## Troubleshooting, cleanup and status

If Chromium is missing, repeat installation. If port 9001 is busy, identify the existing owner; the harness must not adopt an arbitrary server. If a locator stops matching, inspect the accessible name before replacing it with a fragile CSS selector. The harness cleans its server/database; keep evidence screenshots. The three existing journeys passed the dedicated harness during this review; human pilot, assistive-technology review and transfer assertions remain pending.
