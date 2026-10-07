# Lab 09: isolate environments and model an accepted promotion

## Problem, objectives and preparation

Dev and QA have different hostnames, but could still share data or deploy an untested artifact. Inspect the isolation model and define when production promotion is permitted. Bloom emphasis: **analyze, evaluate, create**.

Complete [preflight](README.md), Lab 08, [architecture/factors](../15-architecture-and-twelve-factors.md) and the [environment runbook](../../docs/environments.md). Know Compose interpolation and image digests. Policy modeling needs Python only; optional configuration rendering requires local Docker Compose. All hostnames/keys below are synthetic `.invalid` fixtures, with mock LLM and disabled mail. No application is started and no public DNS is changed. Requirement: [REQ-DELIVERY](../../docs/project/baseline.md#req-delivery).

## Guided policy and configuration checks

```sh
uv run python book/labs/fixtures.py promotion
```

Expected: three unsafe proposals are rejected—different digest, failed QA checks and missing approval—while the same accepted commit/digest/schema plus approval is permitted. Read the function: it is a **local decision model**, not evidence that the real CI promotion gate exists. Issue #24 still owns implementation acceptance.

With local Compose available:

```sh
uv run python book/labs/fixtures.py environments
```

Expected: rendered projects are `is373-ai-chat-dev` and `is373-ai-chat-qa`; app effect settings are mock/disabled; a duplicate-name proposal violates the distinct-name invariant. Rendering validates the model without creating networks/volumes or pulling its synthetic image digest. Inspect [preview Compose](../../deploy/compose.preview.yaml) for private database networks, unique routing/service names and caps.

## Fixed faults and repair

Changing a candidate digest after QA acceptance invalidates the evidence link. Re-running a build and calling it the same release does not repair that link. Sharing a Compose project name risks volume/router collisions even when DNS differs. The smallest repair preserves the accepted artifact and gives each stage independently scoped data/configuration/secrets. Separate app environments on one host still share a kernel, capacity and host-failure boundary.

## Evidence, transfer and reflection

Submit the policy outcomes and an isolation matrix for project, database volume, private network, JWT key, database password, provider effects and release identity. Mark configuration rendering versus actually deployed/verified isolation separately. If Compose is unavailable, submit policy evidence and mark rendering incomplete.

Transfer: propose a promotion workflow with a failing QA test, compatible additive migration, explicit approval and a changed-schema recovery decision. Define acceptance criteria and two alternatives for a GitHub plan without protected-environment approvals. Do not claim a gate exists because the YAML has an environment name. Explain SemVer's declared public contract independently of the image digest.

## Troubleshooting, cleanup and status

Compose parsing failures should name the missing variable/model concern; never supply production `.env` to this lab. The renderer deletes temporary files automatically. The policy model was maintainer-executed during this review. Docker rendering remains authored/unverified here; the recorded public installations are earlier operational evidence. Automated promotion and independent learner assessment remain pending.
