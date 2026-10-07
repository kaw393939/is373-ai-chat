# Lab 08: distinguish tested source, local image and published release

## Problem, objectives and preparation

Someone says, “The image was built, therefore it is deployed.” Construct the evidence chain and reject a mismatched source claim. Bloom emphasis: **apply, analyze, evaluate**.

Complete [preflight](README.md), [delivery](../08-delivery.md) and Lab 07. Know Git commits, image layers and Actions jobs. Use a clean learner checkout of the book edition and a local Docker daemon. The build can download dependencies/base images and consume disk/CPU. This lab does not push images, trigger main deployment or require registry credentials. Requirement: [REQ-DELIVERY](../../docs/project/baseline.md#req-delivery).

## Guided build and trace

Read [Dockerfile](../../Dockerfile), the `image` fixture and [the workflow](../../.github/workflows/delivery.yml). Predict the source label and runtime user before running:

```sh
uv run python book/labs/fixtures.py image
```

Expected: the amd64 build succeeds, the source label equals the current full Git SHA, runtime user is `10001:10001`, a local image content ID is printed, and a deliberately incorrect source claim is rejected. The program refuses a dirty checkout, uses a unique lab tag and removes only that tag afterward. It never invokes `docker push` or SSH.

Construct a five-row release ledger: source SHA, verification run, tested image archive, registry manifest digest and observed deployment commit/schema. Use [recorded implementation evidence](../../docs/implementation-evidence.md) as a historical case; label it with its date instead of claiming the current live state. Explain why the local Docker image ID is not the registry manifest digest.

Read the workflow dependency and permissions boundaries. `publish` depends on `verify`, publishes the saved image, and runs only for main push. Ordinary PR/manual verification must not acquire production credentials. Main currently deploys directly; persistent QA promotion remains separate work.

## Fixed fault and repair

The fixture's fake all-zero source claim cannot match the image's source label. The smallest policy repair is checking provenance before accepting the artifact; relabeling a mismatched image is not proof that its contents changed. In the historical workflow case, consider a second fault: publishing a newly rebuilt image after verification. Explain why source equality alone would not prove byte identity and why the saved tested artifact matters.

## Evidence, transfer and reflection

Submit the build label/ID, rejection checkpoint and release ledger with explicit observed versus unavailable cells. Transfer: design a verify-only CI run for your private fork and an acceptance rule that blocks publication when browser tests fail. Keep deployment secrets absent. Compare signed attestations with source labels: what additional trust must a verifier establish?

## Troubleshooting, cleanup and status

A dirty-checkout rejection asks you to inspect/save relevant local work or use a fresh edition clone; it does not authorize committing unrelated files. Build failures should be recorded at the failed stage. Do not prune globally to solve disk pressure. The unique tag is removed on exit; reusable builder cache may remain. The exact image fixture passed on Linux amd64 in [book CI run 37550661540](https://github.com/kaw393939/is373-ai-chat/actions/runs/37550661540), including the source label, non-root user and mismatch rejection. This workstation lacks Docker; no local macOS image execution is claimed. Human pilot remains pending.
