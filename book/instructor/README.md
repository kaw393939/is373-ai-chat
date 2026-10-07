# Instructor desk: assess a defensible engineering decision

Use the book's [learner evidence record](../labs/README.md) and [Bloom framing](../16-human-judgment-and-ai.md). These materials are an authored instructor pack, not a claim of classroom validation. The [pilot record](pilot-record.md) keeps actual learner evidence and revised instructions separate from maintainer command checks.

## Before teaching

Confirm the edition's source baseline, platform/tool prerequisites and which container activities have been executed. Rehearse the exact commands on a disposable setup. Do not give students shared production credentials. Allocate learner time from pilot observations; no reliable completion-time claim has been measured yet.

An entry diagnostic asks a learner to explain a function call/exception, read a SELECT with a predicate, distinguish a Git commit from a running release, and describe an HTTP request/response. Record gaps and assign the relevant foundation reading. The exercise is diagnostic, not proof of comprehensive prerequisite competence. Learners with limited prior SQL/Git/browser experience need a supported route before the capstone.

During a lab, ask for a prediction before execution. After a passing checkpoint, ask an unseen counterexample. This distinguishes understanding from repeating instructions or submitting AI-generated output. Permit assistive tooling and equivalent evidence formats; assess the contract and explanation rather than typing speed or a particular editor.

## One rubric, calibrated with examples

Score each criterion 0–3. A 2 is the minimum competent result; a 3 adds well-supported transfer. Use weights to communicate emphasis, not manufacture precision. Convert `score/3 × weight` only if a numeric grade is needed.

| Criterion / weight | 0: unsupported | 1: developing | 2: competent | 3: transferable |
|---|---|---|---|---|
| Accuracy / 20 | Materially false contract/attribution | Correct terms with important omissions | Correct behavior, terms and attribution for the inspected edition | Explains exceptions and corrects a plausible misconception |
| Causal reasoning / 25 | Output with no causal account | Lists tools or steps | Connects input, boundary, state and failure to the result | Tests competing explanations and an unseen counterexample |
| Evidence / 25 | No reproduction or unsafe/non-owned target | Passing output without clear target/assertion | Reproducible bounded commands, source ID, meaningful assertion and limits | Failing-then-passing evidence or independent checks with explicit scope |
| Judgment / 20 | Choice justified by authority/fashion | One option with vague tradeoffs | Explicit criteria, alternative and justified decision | Names a measurement/changed constraint that would change the decision |
| Communication / 10 | Unreviewable or secret-bearing submission | Disconnected screenshots/code | Concise trace, focused diff and clear AI-assistance record | Another reader can reproduce and defend the decision |

An otherwise high score does not compensate for using a shared/public destructive target, disclosing real credentials or claiming an unexecuted validation occurred. Return that submission for a safe, truthful replacement. Distinguish a missing prerequisite from a bad engineering choice and give corrective feedback.

## Chapter evidence map

Each row supplies an observable assessment, not a claim that naming a verb establishes Bloom alignment. For technical chapters use the paired lab's checkpoints; historical/concept chapters have evidence assignments below.

| Chapter | Evidence artifact and dominant cognitive task | Competent evidence |
|---|---|---|
| 00 Reading code | Annotated trust-boundary trace; analyze | Names input, validation, durable state, failure and exact function/test |
| 01 System | Browser-to-provider diagram with scoped evidence; understand/analyze | Separates ASGI test path from proxy/TLS path |
| 02 Local | Reproduction record and origin/config explanation; apply | Uses owned setup, records source/tools, explains a rejected origin |
| 03 Data | Generated migration and compatibility matrix; apply/evaluate | Identifies additive change, drift and scoped SQLite evidence |
| 04 Identity | Caller/action matrix and counterexample; analyze | Separates authentication, role and ownership |
| 05 Streaming | Terminal-contract table and fragmented frame; analyze/evaluate | Distinguishes bytes, frames, terminal state and current EOF gap |
| 06 Operations | Limits/usage/reservation comparison; analyze | Distinguishes cap from guaranteed capacity and units from dollars |
| 07 Testing | Negative assertion plus coverage counterexample; evaluate | Demonstrates why passing coverage can miss a defect |
| 08 Delivery | SHA→tested artifact→digest→deployment ledger; analyze | Marks each observed/inferred/unavailable link accurately |
| 09 Hosting | Disposable installation proposal/checklist; evaluate | Includes trust, configuration and capacity/recovery boundaries; no false fresh-host proof |
| 10 Recovery | Original/restored records/schema and recovery inventory; apply/evaluate | Verifies content and names off-host limitations |
| 11 Email | Commit/delivery sequence and outbox-state table; analyze | Distinguishes queued, accepted and received; retains stable retry identity |
| 12 History | Two sourced decisions under historical constraints; analyze/evaluate | Connects a before/after tradeoff to a present decision without inevitability |
| 13 Engineering ideas | Small refactoring proposal with preserved contract; evaluate/create | Uses contributor's idea accurately, chooses a useful boundary and rejected abstraction |
| 14 Agile/community | Compared primary sources and measured process improvement; analyze/evaluate | Explains shared values, different approaches and an observation that tests the proposal |
| 15 Architecture/factors | REST/twelve-factor distinction plus two topology proposals; evaluate | Uses explicit traffic/availability/cost criteria and identifies unproved factors |
| 16 Human judgment/AI | Capstone issue, decision, focused change and defense; create | Meets agreed acceptance with bounded reproduction, reviewed AI work and remaining uncertainty |

Do not grade “remember” out of the course: vocabulary/attribution accuracy is necessary. Add a brief retrieval check before each trace, then assess how the learner uses that knowledge. Creation can require returning to syntax and definitions; the categories do not imply a rigid staircase.

## Acceptable explanations and common misconceptions

| Prompt | Acceptable core answer | Misconception to challenge |
|---|---|---|
| What does a signed JWT establish? | Claims integrity/authenticity under the signing-key policy; issuer/audience/expiry and current account/session/ownership still matter | “Signed means encrypted” or “a role claim grants access forever” |
| Why do the adapters need a contract? | Clients depend on success/failure/cancellation semantics, not just a method name | “Two `stream` methods imply substitutability” |
| Why does 100% coverage miss the mutant? | A positive-only assertion reaches code but does not distinguish the forbidden behavior | “Executing every branch proves correctness” |
| Why not roll back every failed migration automatically? | Prior code may be incompatible; data-changing downgrades can destroy evidence/data | “Previous image implies safe previous schema” |
| What does outbox success mean? | Committed intent, provider acceptance and inbox delivery are different evidence boundaries | “The transaction committed, so mail arrived” |
| Is this API fully REST/hypermedia-driven? | Current client knows routes; HATEOAS needs usable advertised transitions/media-type semantics | “JSON plus HTTP is sufficient REST” |
| Did a famous contributor invent the whole practice? | Use the original claim and describe collaborators/predecessors/context | A name or principle substitutes for historical evidence or design criteria |

## Capstones with multiple defensible decisions

**Partial stream:** a typed terminal event can centralize policy; adapter-side validation can preserve a smaller interface. Accept either when success/failure/cancellation are explicit, fake transport reproduces the fault, partial text behavior is tested and compatibility costs are addressed. Reject silent success on unexplained EOF.

**Conversation collaboration:** explicit membership roles can support fine-grained sharing; an administrator-only support workflow can suit a deliberately narrower product. Accept decisions matching the stakeholder's stated need and least-privilege/ownership tests. Reject broad access justified only by the existence of a login or admin button.

**Environment topology:** capped shared-host previews can meet a low-cost teaching need; separate infrastructure can meet stronger isolation/availability goals. Accept either with a budget, capacity/failure analysis, synthetic data controls and truthful promotion/recovery evidence. Reject saying hostnames alone isolate workloads.

**Interface focus:** native dialog semantics or a carefully tested custom implementation can both work. Require initial focus, keyboard containment as appropriate, Escape policy, error announcement and focus restoration evidence. Reject a screenshot as the only accessibility proof.

No “model solution” removes the need to assess constraints. For an oral defense, change one assumption (tenfold traffic, missing usage metadata, concurrent refresh, unavailable paid GitHub gate) and ask whether the chosen design still fits. Score reasoning rather than agreement with the instructor's preferred framework.

## Instructor records and feedback loop

Keep rubric scores, observed stuck points and revised instructions with the edition/pilot identifier. Human pilot records contain consented learner observations and synthetic evidence only. Every lab must distinguish command verification, independent human instruction-following and assessed transfer. Use learner feedback to revise one representative lab before scaling the entire course; maintain the same safety/verification distinction in chapter claims.
