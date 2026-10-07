# Lab 12: defend and deliver one engineering decision

## Problem, objectives and preparation

AI can generate a plausible repair quickly. Your job is to choose a valuable outcome, challenge the proposal and supply evidence that the change meets its contract. Bloom emphasis: **analyze, evaluate, create**.

Complete [preflight](README.md), Labs 02/04/05/07 and [human judgment](../16-human-judgment-and-ai.md). Work in a private learner fork/disposable local branch. No main push, paid provider, public fault or real email is required. Requirement: [REQ-LEARNING](../../docs/project/baseline.md#req-learning). The [instructor guide](../instructor/README.md) provides a rubric, not one mandatory architecture.

## Fixed case and safe reproduction

Use this edition's case: **partial provider text followed by unexplained EOF must not be described as completed work**. Stakeholder consequence: a user may trust an incomplete answer and an operator loses a reliable distinction between complete/failed runs.

```sh
uv run python book/labs/fixtures.py stream
```

Expected: the fixture demonstrates the normalized delta-only EOF gap and the Unicode boundary. Inspect `generate` to explain how the application currently derives its durable terminal state. If a later edition repairs the adapter, use the fixed delta-only fake to exercise the same contract; record the baseline instead of hunting a new live production defect.

## Proposal, implementation and evidence

1. Write a one-page issue record: stakeholder need, baseline requirement, observed reproduction, explicit non-goals and acceptance criteria. Example: explicit completion ends complete; unexplained EOF ends failed with partial text; cancellation remains cancelled; no real API call occurs; no automatic paid retry is added.
2. Compare at least two designs. A typed provider terminal event and adapter-side completion validation are possible approaches; neither is accepted merely because it names a pattern. Explain compatibility, observability and maintenance cost.
3. Ask AI for a proposal if useful. Record assumptions, inspect generated code and correct one mistake or independently verify one non-obvious claim. Write the failing contract assertion before accepting the repair.
4. Implement one small slice in your private checkout. Preserve synthetic fixtures and target guards. Separate behavior change from unrelated cleanup; use an atomic commit referencing your issue record. Do not close a real shared-project issue solely because a local demonstration passes.
5. Run the selected provider/integration tests using the temporary environment:

```sh
env -u TEST_DATABASE_URL -u DATABASE_URL uv run pytest -q tests/unit/test_providers.py tests/integration/test_chat.py
```

Expected after your repair: relevant tests pass, including your new negative EOF assertion. A PostgreSQL-only test can skip here; name that limitation and use Lab 07 for genuine locking evidence when relevant. A passing unchanged suite without the new assertion is insufficient capstone evidence.

## Defense and transfer

Submit the issue record, alternatives/decision, failing-then-passing assertion, focused diff, source/commit identifiers, operating consequence and remaining uncertainty. Explain how to recover or disable the change if its assumption proves wrong. An assessor asks one unseen counterexample, such as success without usage metadata or cancellation during completion. Explain how your declared contract handles it.

An alternative capstone may improve ownership membership, migration compatibility or dialog focus using a fixed synthetic case. Agree on equivalent acceptance/evidence first; assess engineering judgment rather than code volume. Reflection: what information would change your decision, and which part requires a human stakeholder instead of another prompt?

## Troubleshooting, cleanup and status

If the new assertion passes before the repair, verify that it actually exercises the fault. If unrelated tests fail, classify regression versus unavailable prerequisites before excluding them. Keep private commits/evidence; remove only disposable services created by prior labs. This capstone is an authored assessment design. It is not a claim that the EOF issue is repaired, every learner finishes it, or the textbook has passed an independent human pilot.
