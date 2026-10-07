# Start here: the reader's guide

*From Request to Release* is for a programmer who can build a small program and wants to reason about an entire web system. A chat application gives us one continuing case: a person signs in, saves a private conversation, receives a streamed reply, and expects that data and access to survive the next deployment. We study the decisions that make those expectations reasonable.

The book connects practical work with the people, history and ideas behind it. Its outcome is an engineer who can explain a boundary, inspect an AI-generated implementation, choose evidence, diagnose failure and defend a strategy. It is not a Python-from-zero course or an exhaustive reference for every library in the stack.

## Entry skills and a bridge

Before the main labs, you should be able to read a short function with parameters, conditionals and a return value; edit a text file; run a command from a named directory; and distinguish source code from the running program. Prior production deployment experience is unnecessary. Familiarity with Python, browser tools and SQL helps; the [foundations bridge](foundations.md) provides a small reading exercise and official learning sources for those gaps.

| Entry question | If you cannot yet answer it |
|---|---|
| Which input causes this function to take its failure branch? | Work through the bridge's Python reading exercise. |
| What method, path and status did a browser request use? | Work through its HTTP/browser exercise. |
| What does a row represent, and what makes its identifier unique? | Read its data and transaction section before the migration chapter. |
| Which process reads a configuration value? | Read its process/network section before local setup. |
| Can you inspect a diff and identify the change? | Use its Git section before modifying code. |

This bridge is an orientation, not a substitute for practicing basic programming. Readers teaching themselves may pause for the linked tutorials. Instructors should use these questions as an entry diagnostic rather than assume that successful installation establishes every prerequisite.

## Equipment, access and cost

The first complete local route needs a Git checkout, a working Docker Engine with Compose v2, a browser and a terminal. Docker builds the Python and frontend runtimes. The source-development and Python lab routes additionally use the repository's Python 3.14.7/uv workflow; frontend source work uses Node 24. See [local development](02-local.md) for the difference between these routes.

The default mock model and disabled email require **no paid model API key, domain, cloud server or transactional-email account**. Downloads and local CPU, memory and disk are still required; first builds need network access. Choose a local container runtime whose installation and license fit your setting. The book does not assume that every vendor's desktop license is free for every reader.

Cloud deployment is a later, optional expenditure requiring an account, domain access and an approved budget. A real model or sender can also introduce usage charges. The mock labs cannot establish real-provider latency, billing or inbox delivery. No learner needs project administrators' credentials to complete the local core.

Use synthetic accounts and prompts in a learner-owned local environment. Shared public dev/QA are coordinated acceptance environments, not disposable student databases. Production is an observation target only when an exercise explicitly permits a read-only check. Database tests clear application tables; test URLs must name dedicated disposable databases.

## Routes through the course

The [book index](README.md#one-course-four-connected-parts) is the single ordered contents list.

- **Full course:** read the origins and engineering ideas, build locally, trace identity/data/streaming, then test, deliver, operate and defend a capstone.
- **Installation first:** local chapter → system trace → identity chapter → request-trace and token labs. Return to the origins before making architectural recommendations.
- **Experienced reviewer:** code-reading method → data and identity → architectural constraints → delivery/recovery. Challenge the application's claims against code and evidence, then choose a focused lab.

A reader who wants to specialize can go deeper in the UI, API/data or delivery/operations while retaining enough breadth to explain the whole request. That is the T-shaped learning goal: depth in one area and useful connections across the others.

## How to use AI and show learning

AI may propose explanations, changes and tests. Record the assistance, inspect the generated work and identify an assumption you checked. You remain responsible for authorization boundaries, data effects, cost and acceptance. A fluent explanation or passing command is a starting observation, not proof of understanding.

For a lab, submit reproducible evidence and a short causal account: what happened, why, which alternative you rejected and what remains unproved. The [Bloom-based assessment chapter](16-human-judgment-and-ai.md) makes recall, explanation, application, analysis, evaluation and creation distinct tasks. Moving toward strategy still requires accurate technical foundations.

## What is ready today

This repository contains a working case study, authored foundation material, expanded sample chapters and laboratory drafts. Later chapters and advanced labs require further development. Command verification, application tests, independent learner success and publication readiness are different claims. Each lab identifies its evidence and limits; human pilots and complete course validation remain outstanding.

Live product acceptance lives in [GitHub issues](https://github.com/kaw393939/is373-ai-chat/issues); the [baseline](../docs/project/baseline.md) defines stable requirements. Study a named checkout and record `git rev-parse HEAD` with evidence. A live website or a subsequently closed issue can differ from the source you read. The book teaches how to detect and explain that difference.
