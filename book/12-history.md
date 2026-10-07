# Before this stack: the problems that persisted

A tool's history is useful when it reveals the problem it addresses. This is not a story in which each new framework replaces everything before it. File-based programs, SQL scripts, server-rendered pages, virtual machines and manual release steps still have valid uses. Our task is to choose deliberately for this system.

**Learning outcomes:** connect a historical constraint to a design choice; distinguish individual contribution from collective work; compare an earlier alternative with this app; evaluate where a historical analogy stops being useful. Dates and original accounts are collected in the [bibliography](references.md).

## Guido van Rossum: a language shaped by practical work

In his own account, Guido van Rossum describes starting Python during the 1989 Christmas holiday and drawing on experience with ABC. Read that account as a design story: an engineer wanted a useful language for real work, informed by an earlier language's strengths and constraints. [Guido's foreword and official history](references.md#ref-python). The FAQ also explains the Monty Python connection behind its name.

Guido describes a specific frustration with ABC: adding new primitive operations to a closed system was difficult. His account also credits Modula-3, and notes that Python's first implementation ran on a Mac despite an intended Unix/C audience. This is a concrete design episode about extension and portability, not a story that Python appeared fully formed. The subsequent mailing-list community supplied criticism and contributions. When choosing a language, ask which extension points and collaboration practices help a real workload. [First-person account](references.md#ref-python).

**Case analysis:** Python makes our API, tests, migrations and operations scripts readable within one language ecosystem. That does not make every task a good fit for Python or make asynchronous correctness automatic. Compare a short SQLAlchemy use case with direct SQL: which version communicates the invariant more clearly? Which language/runtime properties would matter if the workload changed from network-bound chat to heavy computation?

The people behind a language also inherit maintenance responsibilities. A convenient dependency today becomes a compatibility decision during upgrades. Students should connect readability and ecosystem choices to locked dependencies and reviewable changes, rather than treating language preference as strategy.

## Linus Torvalds: collaboration changes the tools

The Linux Foundation records Torvalds's 1991 announcement of his kernel project. Linux's subsequent history involves a large community, not one developer building every part. [Linux Foundation account](references.md#ref-linux). Distinguish the kernel from distributions and the many user-space tools that make a usable system.

Git's official history describes Linux development's earlier patch exchanges, use of BitKeeper, and the 2005 change that led Torvalds and the community to develop a new distributed version-control system. Speed, distributed work and support for nonlinear development were practical requirements. [Git's history](references.md#ref-git).

The Git account describes a constraint reversal: losing access to the previous collaboration tool forced a replacement decision. The response prioritized distributed work, speed and nonlinear development. In our much smaller project, those capabilities still permit local experimentation, but do not decide whether an experiment should enter production. The same tool supports different governance because the participants' scale and responsibilities differ. [Official Git history](references.md#ref-git).

**Case analysis:** our atomic commits are a way to make intent and review tractable. Git supplies history, branches and identities; GitHub supplies hosting, issues and Actions. Those are distinct tools. Neither decides which changes belong together or whether a production release is appropriate.

**Discussion:** compare a centrally controlled repository with distributed local histories. Why would kernel collaboration motivate one choice? Which benefits matter in a small student team, and which governance problems remain either way?

## From files and pointers to relational data

An application can store records in files and implement lookup, update and consistency itself. Other database approaches organize records through explicit navigational structures. Those choices can work well, but application code must understand how records are reached and related. A relational approach expresses data as relations and lets queries describe the desired result. It shifts work into a database engine; it does not remove the need to design constraints and transactions.

PostgreSQL's own history traces POSTGRES to a Berkeley project beginning in 1986, Postgres95 to the introduction of an SQL interpreter, and the PostgreSQL name to 1996. That lineage predates today's Python web stack. [Official PostgreSQL history](references.md#ref-postgres-history).

The official account names Michael Stonebraker's Berkeley leadership and Andrew Yu and Jolly Chen's addition of an SQL interpreter in 1994. A research prototype's growing support burden and a community's later maintenance choices are part of the history, alongside technical features. An engineer choosing PostgreSQL now inherits decades of database work; SQLAlchemy is a later application interface, not the origin of relational thinking. [Project account](references.md#ref-postgres-history).

Here, a conversation and its messages have ownership and foreign-key relationships. SQLAlchemy translates Python expressions and manages mapped objects; it does not make SQL or transaction design disappear. Before an ORM, an engineer could issue parameterized SQL and map rows manually. That remains an alternative when direct query control is clearer. Before migration tooling, teams could maintain numbered SQL scripts and an execution ledger. Alembic automates part of that discipline, while review still decides compatibility and recovery. Follow [models](../app/models.py), [database construction](../app/db.py) and [the data chapter](03-data.md).

**Discussion:** Which invariant belongs in a database constraint, which in a transaction, and which in application policy? What would an ORM fail to protect if the database allowed inconsistent rows?

## From linked documents to interactive applications

The W3C history records Tim Berners-Lee's 1989 proposal at CERN and the early implementation of Web clients and servers. The Web's initial document-sharing problem helps explain why URLs, links and HTTP still underpin a modern application. [W3C historical account](references.md#ref-web).

An early-style website can return complete HTML for each action. Browser scripting and asynchronous requests allow a page to update parts of its interface without navigation. React organizes client rendering and state, but server-rendered forms remain a reasonable alternative for many products. This chat needs incremental responses and conversation state; it also inherits the complexity of races, stale results and keyboard usability. Those problems are part of engineering the UI, not automatically solved by a library.

Polling asks repeatedly whether new output exists. A long-lived streamed response can deliver updates as they arrive. Our Fetch/SSE reader must handle partial frames and Unicode boundaries; choosing streaming trades repeated requests for connection lifetime and cancellation complexity. WebSockets are another option when the interaction needs bidirectional messages over one connection. See [streaming](05-streaming.md) and [frontend code](../frontend/src/api.ts).

**Discussion:** Would server-rendered pages plus a small streaming script satisfy this app? What would be simpler, and what state would still need management?

## From server sessions to signed access tokens

An opaque cookie can identify a session whose details reside on the server. A signed access token carries verifiable claims that services can inspect. Both designs need careful expiry, theft protection and authorization. JWT payloads are readable; signing does not encrypt them. Token format also does not decide where revocation state belongs.

This app combines short-lived signed access tokens with durable session families and rotating opaque refresh tokens. The database participates in current account and revocation checks. A token valid at issuance can outlive a role change unless current policy is checked. Read [identity](04-auth.md), [security](../app/security.py) and the [token lab](labs/01-token-boundaries.md).

**Discussion:** When would a straightforward server-side session be preferable? What additional complexity are we accepting by using this hybrid design?

## From configured machines to packaged processes

A deployment can install Python, libraries and an application directly on a host, with a service manager starting it. Repeating that process by hand can create drift between machines. Scripts, configuration management and virtual machines address different parts of that problem. Containers package a process and its dependencies, while the host kernel and external configuration still matter.

Docker's account dates its open-source Engine launch to 2013. Docker made container packaging accessible; it did not invent operating-system isolation, and a container is not a separate machine. [Docker's container explanation](references.md#ref-docker).

Our multi-stage build keeps frontend build tools and Python installation tools out of the runtime. Compose declares services, networks, volumes and limits. Persistent data stays outside replaceable app containers. A resource cap bounds one container's consumption; it does not reserve a dedicated server or remove shared-host failures. The deployed dev/QA/prod examples make that distinction visible. See [Dockerfile](../Dockerfile), [Compose](../deploy/compose.preview.yaml) and [environment evidence](../docs/environments.md).

**Discussion:** What must be backed up to recover the system if every app container disappears? What if the entire host disappears?

## From release weekends to short feedback loops

Teams can integrate large batches late and manually deploy a selected build. Frequent integration brings incompatibilities forward while changes are smaller; automated checks make that feedback repeatable. Continuous integration is a team practice, not merely a hosted workflow file. [Fowler's CI explanation](references.md#ref-ci).

Continuous delivery aims to keep changes deployable and make release predictable. It does not require automatically publishing every commit to users. [Continuous Delivery](references.md#ref-delivery). Our pipeline already tests an image before publishing and deploying it, but persistent QA-gated promotion remains open. Students should distinguish implemented checks from the intended delivery policy.

The 2001 Agile Manifesto came from a gathering of seventeen practitioners representing several approaches. It articulated shared values rather than inventing every iterative technique or prescribing a project-management product. [First-person history](references.md#ref-agile). A comprehensive textbook and useful agile feedback can coexist when explanations serve learning and maintenance rather than replace working evidence.

**Discussion:** What would you automate first in a manual release, and what evidence would justify handing that action to a workflow?

## Engineering with AI

AI assistance changes how quickly candidate code and explanations can be produced. In this case study, a human still selects valuable outcomes, defines boundaries, approves costs and checks integration and recovery. A generated comment can be wrong even when a generated test passes. Treat the repository, executed evidence and cited original work as the material to inspect; fluency is not verification.

The capstone asks the learner to explain an issue's business consequence, reproduce it safely, make a small justified change and demonstrate acceptance. That is how the history connects to current practice: old coordination, abstraction and reliability problems continue inside new tools.

**Synthesis exercise:** choose one transition above and draw its before/after boundary. Explain a problem solved, a responsibility retained and a new cost introduced. Apply that comparison to a current issue without claiming the older solution was universally inferior.
