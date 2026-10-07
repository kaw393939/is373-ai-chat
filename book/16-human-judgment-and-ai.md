# Learning to direct, evaluate and create with AI

The revised Bloom taxonomy distinguishes remembering, understanding, applying, analyzing, evaluating and creating. It supports designing learning objectives and evidence, rather than treating every completed activity as the same kind of achievement. [University of Illinois Chicago teaching guide](https://teaching.uic.edu/cate-teaching-guides/syllabus-course-design/blooms-taxonomy-of-educational-objectives/).

We use those categories to design the course, not to declare that engineers climb a rigid ladder once and stop using earlier skills. Evaluating a migration may require returning to SQL syntax. Creating a release strategy may require learning unfamiliar hosting constraints. Technical understanding remains necessary when an AI tool writes the implementation.

## Objectives and evidence

By the end of this chapter, a learner should be able to:

1. Distinguish a remembered definition from a causal explanation using a JWT or migration example.
2. Analyze one generated suggestion against a trust boundary and an executed counterexample.
3. Evaluate two designs using stated user, reliability, cost and maintenance criteria.
4. Create a small change with acceptance criteria, scoped validation and a justified recovery decision.

The assessed artifacts are a before/after explanation, an alternatives/decision record, a focused diff and a defense of an unseen counterexample. [Lab 12](labs/12-strategy-capstone.md) supplies the bounded case and commands; the [instructor guide](instructor/README.md) defines competent versus unsupported evidence. Use the [laboratory preflight](labs/README.md) before any executable activity.

| Cognitive task | Activity in this case study | Evidence to assess |
|---|---|---|
| Remember | Identify a JWT claim, factor or engineering contributor | Correct definitions and attribution |
| Understand | Explain why a JWT signature does not establish conversation ownership | A request trace with boundaries and counterexamples |
| Apply | Run a local expiry experiment or an additive migration | Reproducible output and a correct interpretation |
| Analyze | Diagnose a cross-tab refresh race or failed provider stream | Reproduction, causal explanation and competing hypotheses |
| Evaluate | Compare server sessions with JWTs, or shared-host QA with separate infrastructure | Explicit criteria, tradeoffs, evidence and a justified choice |
| Create | Design and validate a release policy or useful business feature | Coherent proposal, acceptance criteria, reviewed implementation and operating evidence |

## History helps explain choices

Guido's account of language design, the Agile participants' search for common ground and Git's response to kernel collaboration each begin with a person facing constraints. Read the [history](12-history.md), [engineering ideas](13-engineering-ideas.md) and [Agile chapter](14-agile-and-community.md), then ask what problem existed, which alternatives were available and what the chosen approach made harder.

A story supplies context, not proof that the same solution is best here. Test the analogy. A small teaching app does not have Linux's collaboration scale; a chat API does not become hypermedia-driven merely because it uses HTTP. This habit connects historical understanding to strategy.

## Division of work with AI

The learner owns the problem, constraints, acceptance and review. AI can propose code, tests, explanations and alternatives. The learner must inspect the dependency boundaries, verify that a test addresses the failure, identify missing integration evidence and decide what is ready for users. These are assessed responsibilities in this course, not a prediction that future implementation will never require human work.

Record which assistance was used and one place where a generated suggestion needed correction. Do not grade the ability to produce a large amount of code. Grade the ability to explain a small coherent change and its consequences.

Consider a fluent generated claim: “All requests are safe because JWTs are signed.” A learner first remembers what a signature establishes, then traces current account/session and ownership checks, reproduces a forbidden cross-account request, and evaluates whether a simpler opaque session would meet the requirements. The same learner may then create a collaborator policy. These activities require different evidence; a paragraph naming Bloom's six categories supplies none of that evidence by itself.

For a formative check, classify three submissions: a diagram listing tools; a trace identifying where a forbidden request is rejected; a compared design with a measurement that could reverse its choice. Explain what each demonstrates and what it lacks. Assessors should look at the work rather than promote an activity's cognitive level solely because its instructions use the verb “evaluate.”

## A strategy-focused capstone

Choose an actual issue from the [canonical backlog](../docs/project/backlog.md). Interview the stakeholder or use an explicitly stated requirement. Describe the business consequence, constraints and two possible solutions. State what you know, what you assume and which measurement could change your choice.

For reproducible assessment, [Lab 12](labs/12-strategy-capstone.md) also supplies a fixed partial-stream scenario. A live issue may change or close while a course is in progress; retain the edition's controlled case and record source identity. Do not create a public failure to keep a capstone interesting.

Then create the smallest useful slice. Use a disposable environment, review the AI's proposed changes, demonstrate the acceptance criteria and connect the issue to atomic commits and evidence. Explain maintenance cost, recovery boundaries and one remaining uncertainty. An implementation that works once but cannot be explained or safely operated is incomplete evidence.

An instructor evaluates factual accuracy, causal reasoning, quality of alternatives, relevance of evidence and clarity of the final decision. A second reader should reproduce at least one lab before we claim that the teaching material itself is validated. Strategies and advanced labs remain authored proposals until their implementation and assessment are demonstrated.

The [rubric and chapter evidence map](instructor/README.md) operationalize these criteria with performance levels and multiple defensible decisions. The [human pilot record](instructor/pilot-record.md) remains pending until a human learner follows the instructions and an assessor records what happened. Maintainer execution, CI success, instruction usability and demonstrated transfer are separate observations; report each accurately.
