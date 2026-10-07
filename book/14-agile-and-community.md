# Agile: people looking for better ways to work

The Agile Manifesto emerged from seventeen practitioners meeting at Snowbird in February 2001. The participants came from several methods rather than one uniform school. The first-person account describes a search for common ground amid dissatisfaction with heavyweight development processes. [Original history](references.md#ref-agile).

**Learning outcomes:** distinguish values from a method or ceremony; recognize all seventeen participants without reducing them to labels; compare their assumptions; evaluate an actual issue/commit/feedback cycle. Read the [engineering ideas](13-engineering-ideas.md) and [bibliography](references.md#ref-agile).

Highsmith's account situates the meeting at a ski resort and describes participants representing Extreme Programming, Scrum, DSDM, Adaptive Software Development, Crystal, Feature-Driven Development and Pragmatic Programming, among others. That range matters: common values could emerge without agreement on one method. The meeting did not create every iterative practice or settle every dispute about design. [First-person account](references.md#ref-agile).

The human story matters: people who disagreed about techniques could still agree on useful values. A framework, board or job title does not reproduce that agreement automatically. In this project, the practical question is whether people can discover a valuable need, inspect working evidence and change direction without losing reliability.

## The four values in practice

The declaration favors human interaction, working software, customer collaboration and responding to change, while acknowledging value in processes, documentation, contracts and plans. [Original declaration](references.md#ref-agile). We paraphrase rather than reproduce part of its specially licensed text.

| Tension | Application to this project |
|---|---|
| People and process | Issues aid coordination; conversations establish intent. An acceptance checkbox cannot replace understanding the user's goal. |
| Software and documentation | Run the app and test the lab. The textbook explains decisions and helps another person reproduce them; documentation volume is not progress. |
| Collaboration and agreements | Confirm desired behavior with the user, and maintain explicit boundaries for costs, data and deployment. |
| Change and plans | Public dev/QA became an additional requirement. Update the topology and acceptance evidence while preserving the original production goal. |

The accompanying twelve principles discuss frequent useful delivery, collaboration, sustainable pace, design quality, simplicity and reflection. [Original principles](references.md#ref-agile). A speed-focused AI workflow that creates unreviewable changes or overwhelms operators should be evaluated against those principles, not celebrated solely for code output.

## Meet every original signatory

The following orientation uses the authors' historical accounts, not assertions about their current jobs. Several already have deeper discussions in [engineering ideas](13-engineering-ideas.md). Read the [original author biographies](references.md#ref-agile) alongside the [official signature list](references.md#ref-agile).

| Person | Starting point for their contribution |
|---|---|
| Kent Beck | Extreme Programming |
| Mike Beedle | Scrum and XBreed |
| Arie van Bennekum | DSDM |
| Alistair Cockburn | Crystal |
| Ward Cunningham | Patterns and incremental development |
| Martin Fowler | Refactoring |
| James Grenning | Embedded development |
| Jim Highsmith | Adaptive Software Development |
| Andrew Hunt | Pragmatic programming |
| Ron Jeffries | Extreme Programming coaching |
| Jon Kern | Delivering business value |
| Brian Marick | Testing |
| Robert C. Martin (“Uncle Bob”) | Design principles |
| Steve Mellor | Modeling |
| Ken Schwaber | Scrum |
| Jeff Sutherland | Scrum |
| Dave Thomas | Pragmatic programming |

This table is an entry point, not seventeen complete biographies. A person's work spans more than one label. Expanded profiles must use that person's original work, distinguish historical claims from present-day descriptions, and connect the idea to a concrete design question. Do not attribute collective work to one famous participant.

## Worked case: change without hiding incomplete work

The user added public dev and QA after production existed. A rigid plan could ignore that request; an unbounded change could silently copy production credentials/data into previews. Our working agreement instead updates the requirement, implements a small isolated slice and records the missing promotion gate. This is our case analysis, not a claim that the signatories prescribed this workflow.

Working evidence now includes distinct databases and credentials; delivery-policy acceptance remains open. A retrospective can ask whether that slice enabled useful feedback, what uncertainty it exposed and whether the next issue addresses that uncertainty. Counting issue closures alone would miss the distinction.

## Discussion laboratory

Choose two participants with different approaches. Find a primary source from each and describe the development problem each was trying to solve. Compare their assumptions about feedback, modeling, testing and coordination. Then examine an actual project issue: which idea helps decide the next step, and where does it leave unanswered questions?

For a retrospective, inspect one change through request → issue → atomic commits → tests → deployment evidence. Identify a delay or misunderstanding, propose one process improvement and define how to observe its effect on the next change. Do not add a ceremony without a problem it is meant to solve.

For assessment, submit a justified choice and a rejected alternative. Naming a signatory demonstrates recall; explaining and testing a strategy demonstrates a different level of learning.
