# 6 · Limits at two layers

A chat can be correct for one user and fail when several users arrive together. The administrator must distinguish an application admission limit from the machine's capacity. The dashboard helps inspect that boundary; it does not make an overloaded host reliable by displaying a green chart.

**Learning outcomes:** distinguish ceilings, reservations and observed usage; trace atomic admission; interpret missing/stale monitoring; propose a capacity experiment with explicit cost and failure criteria. Read [transactions](03-data.md) and [streaming](05-streaming.md) first.

## From machine inspection to service questions

An operator can inspect processes and disk space manually. Those checks answer a momentary machine question, while a service owner also needs to know whether users can accomplish their task. In Google's 2016 site reliability engineering (SRE) book, Rob Ewaschuk explains monitoring through latency, traffic, errors and saturation. That vocabulary connects observations to operating decisions; Google did not invent the need to observe systems. [Original chapter](references.md#ref-sre).

Our small deployment supplies host/container samples and administrative usage, not the complete monitoring system described there. It lacks an independently verified external alerting service. A healthy database readiness request also does not prove that a real model or sender can serve users.

## Worked case: two requests, one remaining allowance

Imagine a synthetic account with one daily request remaining. Two workers both read the old count before either writes. Without shared coordination, both could approve work. `prepare_run` locks a shared budget row and the current account, examines active runs and daily usage, then reserves capacity in the same admission transaction. PostgreSQL row locks serialize competing decisions across app workers; an in-process semaphore would only coordinate one worker.

A reservation counts UTF-8 input bytes plus maximum output tokens. It deliberately mixes conservative admission units rather than pretending to predict exact provider billing. Failed or cancelled runs keep their reservation because upstream work might already be billable. Actual reported provider usage is recorded separately. An administrator must not interpret either a Docker memory cap or a daily reservation as a dollar-spending guarantee.

Docker supplies a second layer. Production caps the app at 512 MiB/0.75 CPU and PostgreSQL at 256 MiB/0.5 CPU. Dev/QA use smaller separate caps. These are maximums, not dedicated reservations; the CPU ceilings can sum beyond the host's one core, and other workloads also consume resources. Memory limits bound a container and can lead to termination when exceeded. [Docker resource documentation](references.md#ref-docker-limits).

## Read the implementation

| Symbol/file | Question |
|---|---|
| [`prepare_run`](../app/services.py) | What lock order, checks and commit make admission one decision? |
| [`RoleBudget`, `DailyUsage`, `Generation`](../app/models.py) | Which limits and leases survive process replacement? |
| [Production Compose](../deploy/compose.yaml), [preview Compose](../deploy/compose.preview.yaml) | What are the CPU, memory, PID and log ceilings? |
| [Host collector](../deploy/host-metrics.py) | Why publish selected aggregates by atomic file replacement? |
| [`Admin`](../frontend/src/Admin.tsx), [metrics types](../frontend/src/contracts.ts) | How are missing samples, samples older than 90 seconds and optional backup freshness displayed? |

The host-only collector reads CPU/memory/disk and selected container summaries. A timer publishes a JSON file mounted read-only into the app. Admin authorization controls its API exposure; the app has no Docker socket. Thirty-second sampling retains 60 samples, about 30 minutes of recent history. This avoids granting container control to a web process, at the cost of a host-specific installation dependency.

## Alternatives and limits

A dedicated metrics system and external probes can retain longer histories and alert independently of the host. They add installation, access and maintenance work. A separate database/host changes the shared failure boundary but costs more; replicas multiply connection pools and require termination/concurrency verification. Choose when measurements justify that change, not because a diagram looks more advanced.

The PostgreSQL admission race test establishes a targeted invariant, not sustained-load capacity. See [#8](https://github.com/kaw393939/is373-ai-chat/issues/8) for replica/termination proof and [#5](https://github.com/kaw393939/is373-ai-chat/issues/5) for account-side firewall/alert evidence.

**Laboratories:** [Lab 07 — admission and coverage](labs/07-admission-and-coverage.md) and [Lab 10 — resources and recovery](labs/10-resource-recovery.md). **Evaluate:** propose traffic, latency, error and saturation measurements before raising concurrency; explain one observation that would make you reverse that decision.
