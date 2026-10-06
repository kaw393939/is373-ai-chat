# People, ideas and engineering judgment

Software engineering develops through research, shared practice and criticism. The people here provide vocabulary for reasoning about change. They are not authorities whose names settle a design question. The application examples below are our interpretations of their ideas, not claims that they endorsed this project.

## Martin Fowler: improve a working design in small steps

Fowler's *Refactoring* appeared first in 1999, with a second edition in 2018. Its central technique is restructuring code through small transformations that preserve observable behavior. Tests support that work; adding a feature or changing a policy is a separate change, even if performed nearby. [Author's account](https://martinfowler.com/books/refactoring.html).

His *Patterns of Enterprise Application Architecture* records recurring approaches to domain logic, relational persistence, presentation and concurrency. Frameworks can implement such patterns while leaving important choices to their users. [Author's account and contributors](https://martinfowler.com/books/eaa.html).

**In this app:** SQLAlchemy already provides session/unit-of-work behavior. Adding a generic repository solely to mention a pattern would need a demonstrated benefit. A useful refactoring instead separates provider transport details from conversation policy and proves behavior remains consistent.

**Exercise:** identify one responsibility mixed into a large function. State what would move, what contract remains, and which test would detect an accidental policy change. Keep that refactoring commit separate from a feature commit.

## David Parnas: hide decisions likely to change

Parnas's 1972 paper compares ways to decompose a system and argues for modules organized around hidden design decisions, rather than merely successive processing steps. [Original paper hosted by Lafayette College](https://www.cs.lafayette.edu/~gexia/cs301/resources/parnas.html).

**In this app:** provider payloads and event formats change independently of account budgets. Putting vendor HTTP details behind an adapter protects that change boundary. A directory name does not provide information hiding if callers still depend on vendor-specific fields.

**Exercise:** list everything outside `providers.py` that would need changing for another text provider. Decide whether each dependency is essential or leaking implementation detail.

## Barbara Liskov and Jeannette Wing: substitution is about behavior

Liskov's work includes programming methodology and data abstraction. [MIT profile](https://www.csail.mit.edu/person/barbara-liskov). Liskov and Wing's 1994 work formalizes behavioral subtyping: a compatible interface must preserve the expectations clients rely on, not merely accept similar method names. [Original paper](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf).

**In this app:** two adapters exposing `stream` are not equivalent if one silently treats an interrupted response as success. The current terminal-event contract needs further work in issues #12 and #18. This is a teaching example of a requirement that has not yet been fully proved.

**Exercise:** define successful termination, failure and cancellation for an adapter. Which assertions could apply to every implementation? Which provider-specific capabilities should remain outside that shared interface?

## Kent Beck: use executable examples to guide small changes

Beck's *Test Driven Development: By Example* teaches development through a sequence of executable examples and small steps. [Publisher's record](https://www.informit.com/store/test-driven-development-by-example-9780321146533). A test should communicate the desired behavior and help choose the next change; its value is not the number of assertions or mock calls.

**In this app:** a cross-account request should fail regardless of how a service is refactored. A test that asserts ownership rejection protects that promise. A test that merely repeats an internal function's current branching can miss the user's real problem.

**Exercise:** write one failing assertion for a real backlog defect, implement the smallest repair, then improve the design while keeping that assertion passing. Explain what the test cannot establish.

## Ward Cunningham: understand the debt metaphor

Cunningham's 1992 WyCash experience report describes incremental growth, broad familiarity with the product and the cost of leaving immature code unconsolidated. His debt analogy explains why shipping an initial understanding can accelerate learning and why failing to revise it makes future work harder. [Original report](https://c2.com/doc/oopsla92.html).

**In this app:** direct main-to-production deployment helped establish a working system, but leaves delivery-policy work once QA exists. Record the consequence and repayment evidence in issue #24. Calling every bug or disliked style “debt” hides the actual failure and cost.

**Exercise:** distinguish a defect, an intentional tradeoff and a missing capability in three existing issues. For each, name the consequence to a user or operator.

## Robert C. Martin: responsibilities follow reasons for change

Martin's explanation of the single-responsibility principle connects responsibility to reasons for change and the people served by that behavior. It does not demand one method per class. [Author's explanation](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html).

**In this app:** browser lifecycle coordination, administrative screens and transport parsing have different reasons to change. Separating them can make UI races easier to reason about. Splitting every line into a helper without clarifying ownership would not achieve that goal.

**Exercise:** name the different consumers and change pressures of one module before proposing a split. Discuss cohesion, navigability and indirection as well as responsibility.

## Alistair Cockburn: separate the application from its surroundings

Cockburn's ports-and-adapters explanation separates application behavior from external interactions so the application can run with different surrounding technologies, including tests. [Original account](https://alistair.cockburn.us/hexagonal-architecture).

**In this app:** the mock provider lets students investigate chat without an external model or paid credential. We use selected adapter boundaries in a modular monolith; we do not claim every route and persistence concern implements a complete hexagonal architecture.

**Exercise:** identify a real test substitution and an external dependency that remains tightly coupled. Would another abstraction reduce a demonstrated cost, or merely increase vocabulary?

## Eric Evans: model the problem with shared language

Evans's domain-driven design work provides a framework and vocabulary for reasoning about complex business domains. [Author's resources](https://www.domainlanguage.com/ddd/).

**In this app:** “approved account,” “session family,” “reservation” and “completed generation” should mean the same thing in discussion, code and tests. A reservation unit is not a billed dollar or necessarily a provider token. Clear language prevents an administrator from interpreting a limit as a financial guarantee.

**Exercise:** write a glossary of five terms with examples and counterexamples. Find one ambiguity that could change a business decision. A small app need not adopt every DDD pattern to benefit from precise language.

## Jez Humble and David Farley: treat delivery as part of the system

Their 2010 *Continuous Delivery* describes automated build/test/deployment pipelines and the surrounding configuration, collaboration and operating practices. [Publisher's record](https://www.informit.com/store/continuous-delivery-reliable-software-releases-through-9780321601919).

**In this app:** a commit, tested image digest, schema and running health response form a release's identity. A successful registry upload is not deployment proof. QA-to-production promotion must preserve the accepted digest; migration and recovery compatibility are separate questions.

**Exercise:** inspect one release's evidence, then explain how a failed QA test must prevent promotion. Mark the current missing gate honestly rather than inferring it from the presence of a QA hostname.

## Compare ideas rather than collect slogans

For any proposed change, ask: what problem does it solve, whose expectation does it preserve, how much indirection does it add, what failure evidence supports it, and what will maintenance cost? Principles can reveal tensions. Information hiding might justify a boundary while navigability argues against unnecessary layers. Resolve that tension using the case, not an author's reputation.

The reading list is a starting point rather than an exhaustive history. Later sections should expand the research, language, human-factors and reliability traditions with equally careful attribution. Historical material and labs should continue to evolve with the project; completed classroom evaluation must be recorded separately from authored material.
