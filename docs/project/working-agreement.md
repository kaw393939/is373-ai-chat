# Working agreement

## Visibility and planning

Use one ordered GitHub backlog. Priority P0 means time-critical continuity, P1 means readiness/correctness, P2 means planned improvement. Each open item has exactly one status label: `status:backlog`, `status:ready`, `status:in-progress` or `status:blocked`. Closed means Done; remove the status label on closure. Area labels and milestones supply filtered views. Select work by priority and dependencies; start one item at a time by default. Do not fabricate owners, sprint dates or story-point estimates.

Milestone goals: M1 production readiness; M2 correctness and architecture; M3 reproducible learning. Review the ready queue and blocked dependencies at each work session. A blocked item names the missing access/decision and the next action; never place credentials in an issue.

## Ready

An issue has a concrete outcome, a baseline requirement/lesson link, evidence classified as reproduced / code finding / unverified operation, observable checkbox acceptance criteria, a validation method and dependencies. Unreproduced code findings start with a regression/reproduction test in an isolated fixture. Split an issue when it has independently releasable outcomes.

## Done

- Item-specific acceptance criteria pass; references to the relevant baseline and lesson remain correct.
- Appropriate unit/integration/browser or operational evidence is linked. Retain the existing coverage gate and explain justified exclusions; never exclude behavior simply to obtain 100%.
- Changes preserve ownership, role checks, secret protection, resource bounds and backward compatibility, or document a reviewed migration/recovery plan.
- Atomic commits reference the issue. A reviewer can see the trigger, resulting behavior and validation from the PR.
- User-visible/runtime changes have deployment and smoke-test evidence before final closure; documentation-only changes have link/content checks. A merged PR alone may leave a deployment issue open.
- Known limitations remain explicit; credentials/private test artifacts are excluded.

## Traceability and atomic commits

Chain: `baseline requirement → issue → branch/PR → commits → tests → release evidence`. Baseline/lessons explain durable intent; issue acceptance criteria describe the current increment. If scope changes, update both the issue and affected canonical explanation.

Use branches such as `codex/12-provider-completion`. A commit contains one coherent change that can be explained and reverted independently, with its supporting test/docs when necessary. Avoid unrelated cleanup. Do not rewrite published history to manufacture atomicity.

```text
fix(stream): reject missing provider terminal events (#12)

Refs #12
Requirement: REQ-CHAT
Validation: provider EOF integration regression
```

Numbers above are illustrative; use the actual issue. `Refs #N` links work without closing it. Use `Closes #N` in a PR targeting main only after all acceptance criteria, including any required deployment evidence, are satisfied; otherwise retain `Refs #N` and close manually with an evidence comment after release. Existing commit-to-issue links are recorded prospectively; older completed work is referenced by its actual release evidence, never invented commits.

An issue closing comment links the PR/commit, test/CI result, deployed commit/digest when applicable and the canonical lesson. Acceptance criteria live in the issue, not copied into PR templates or progress tables.

## Decisions and sources

For a consequential tradeoff, add a short issue-linked ADR under `docs/decisions/`: context, decision, alternatives, consequences and evidence. A routine module extraction does not need an ADR. Revisit assumptions after actual use; evaluate AI output with the same evidence expected from human work.

This is a lightweight agile agreement, not a claim to implement every Scrum ceremony. The [Scrum Guide](https://scrumguides.org/scrum-guide.html) informs the product goal and shared Definition of Done. [GitHub issue/PR linking](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) documents default-branch closing behavior. [Issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) provide structured intake.
