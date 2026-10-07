# References and further reading

This bibliography separates original publications, first-person histories, official documentation and secondary teaching guides. Access dates record when online material was consulted, not the date a technology was invented. Web documentation is living material unless an explicit version is given; the repository's locks determine the installed software. Historical facts come from the listed sources; case-study applications and tradeoff judgments are our analysis.

All online references below were accessed **October 6, 2026**. We paraphrase and link sources rather than reproduce their books, figures or biographies. Linking a source does not grant reproduction rights. The companion's own publication/permission policy is a separate owner decision.

## People and histories

<a id="ref-python"></a>
**Van Rossum, Guido.** “Foreword for *Programming Python*, first edition.” May 1996. First-person account of Python's December 1989 start, ABC/Modula-3 influences and community participation. [Author's text hosted by Python](https://www.python.org/doc/essays/foreword/); [official Python origins FAQ](https://docs.python.org/3/faq/general.html#why-was-python-created-in-the-first-place). Read historical opinions as situated statements, not current runtime benchmarks.

<a id="ref-linux"></a>
**Linux Foundation.** “Linus Torvalds,” in *Leadership*. Undated organizational biography. Supports the August 1991 announcement; the surrounding leadership page contains changing present-day descriptions. [Profile](https://www.linuxfoundation.org/about/leadership). Our chapter distinguishes the kernel from a distribution and credits collective work.

<a id="ref-git"></a>
**Chacon, Scott, and Ben Straub.** *Pro Git*, second edition, “A Short History of Git.” Apress, 2014; online edition maintained subsequently. Describes patch exchange, BitKeeper and the 2005 transition. [Official hosted chapter](https://git-scm.com/book/en/v2/Getting-Started-A-Short-History-of-Git).

<a id="ref-postgres-history"></a>
**PostgreSQL Global Development Group.** “A Brief History of PostgreSQL.” PostgreSQL 17 documentation, living versioned manual. Describes Berkeley POSTGRES, Postgres95 and the PostgreSQL name. [Version 17 history](https://www.postgresql.org/docs/17/history.html).

<a id="ref-web"></a>
**W3C; historical timeline credited to Robert Cailliau and Dan Connolly.** “A Little History of the World Wide Web.” Created circa 1995, with subsequent revisions. Includes Berners-Lee's 1989 proposal and early implementations. [W3C timeline](https://www.w3.org/History.html). A timeline supplies dates; it does not establish that every early site used the same design.

<a id="ref-docker"></a>
**Docker.** “What Is a Container?” Undated official explanation/history. Records Docker Engine's 2013 launch and its use of existing cgroups/namespaces. [Official page](https://www.docker.com/resources/what-container/). Vendor descriptions of portability/security are not unconditional guarantees for our application.

## Engineering ideas and collective practice

<a id="ref-fowler-refactoring"></a>
**Fowler, Martin.** *Refactoring: Improving the Design of Existing Code*. Addison-Wesley, first edition 1999; second edition 2018. [Author's edition record](https://martinfowler.com/books/refactoring.html). Supports behavior-preserving restructuring; feature/policy changes need their own acceptance evidence.

<a id="ref-fowler-eaa"></a>
**Fowler, Martin, with named contributors.** *Patterns of Enterprise Application Architecture*. Addison-Wesley, 2002. [Author's book and contributor record](https://martinfowler.com/books/eaa.html). Pattern vocabulary is a starting point for comparing designs, not a requirement to wrap every ORM operation.

<a id="ref-parnas"></a>
**Parnas, David L.** “On the Criteria To Be Used in Decomposing Systems into Modules.” *Communications of the ACM* 15(12), December 1972, pp. 1053–1058. DOI: [10.1145/361598.361623](https://doi.org/10.1145/361598.361623). [Accessible Lafayette transcription](https://www.cs.lafayette.edu/~gexia/cs301/resources/parnas.html). The transcription explicitly warns that it may not accurately reproduce the original; use the publication/DOI as the bibliographic authority. DOI metadata was checked against the publisher-deposited Crossref record; the publisher article page was unavailable to the audit browser.

<a id="ref-liskov-wing"></a>
**Liskov, Barbara H., and Jeannette M. Wing.** “A Behavioral Notion of Subtyping.” *ACM Transactions on Programming Languages and Systems* 16(6), November 1994, pp. 1811–1841. DOI: [10.1145/197320.197383](https://doi.org/10.1145/197320.197383). [Author-hosted paper](https://www.cs.cmu.edu/~wing/publications/LiskovWing94.pdf); [MIT profile of Liskov](https://www.csail.mit.edu/person/barbara-liskov). Interface shape alone does not prove compatible behavior.

<a id="ref-beck"></a>
**Beck, Kent.** *Test Driven Development: By Example*. Addison-Wesley, first edition; published November 8, 2002, copyright 2003. ISBN 9780321146533. [Publisher record and author preface](https://www.informit.com/store/test-driven-development-by-example-9780321146533). Publication date and copyright year differ; neither implies that automated testing began with this book.

<a id="ref-cunningham"></a>
**Cunningham, Ward.** “The WyCash Portfolio Management System.” OOPSLA experience report, 1992. [Author's report](https://c2.com/doc/oopsla92.html). Read the debt metaphor in the context of consolidating an evolving understanding, rather than calling every disliked line “debt.”

<a id="ref-martin"></a>
**Martin, Robert C.** “The Single Responsibility Principle.” May 8, 2014. [Author's essay](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html). Explains reasons for change and whom a responsibility serves; it is not a one-method-per-class rule.

<a id="ref-cockburn"></a>
**Cockburn, Alistair.** “Hexagonal Architecture.” Author's online account, originally 2005, maintained/rehosted subsequently. [Author's account](https://alistair.cockburn.us/hexagonal-architecture). Our selected adapters do not certify a complete ports-and-adapters architecture.

<a id="ref-evans"></a>
**Evans, Eric / Domain Language.** “Domain-Driven Design.” Undated author's resource collection. [Author's resources](https://www.domainlanguage.com/ddd/). Used for shared language and domain-model reasoning; this app does not claim complete adoption of DDD.

<a id="ref-ci"></a>
**Fowler, Martin.** “Continuous Integration.” Living author article, revised over time. [Author's account](https://martinfowler.com/articles/continuousIntegration.html). Distinguishes a frequent integration practice from a hosted build tool.

<a id="ref-delivery"></a>
**Humble, Jez, and David Farley.** *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Addison-Wesley, 2010. ISBN 9780321601919. [Publisher record](https://www.informit.com/store/continuous-delivery-reliable-software-releases-through-9780321601919); [authors' companion site](https://continuousdelivery.com/).

<a id="ref-agile"></a>
**Beck, Kent, and the sixteen other named signatories.** *Manifesto for Agile Software Development*, 2001. [Original declaration and signature list](https://agilemanifesto.org/); [principles](https://agilemanifesto.org/principles.html); [historical author biographies](https://agilemanifesto.org/authors.html). **Highsmith, Jim.** “History: The Agile Manifesto,” 2001, [first-person history](https://agilemanifesto.org/history.html). The declaration's own notice permits copying only in its entirety through that notice; our chapter paraphrases and links it.

<a id="ref-fielding"></a>
**Fielding, Roy Thomas.** *Architectural Styles and the Design of Network-based Software Architectures*. Doctoral dissertation, University of California, Irvine, 2000, chapter 5. [Original REST chapter](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm). The hypermedia constraint is discussed in section 5.1.5; an HTTP/JSON API is not automatically REST.

<a id="ref-twelve-factor"></a>
**Wiggins, Adam.** *The Twelve-Factor App*. Last updated 2017 according to the source footer. [Original document](https://12factor.net/), including twelve linked factors. Records Heroku experience and inspiration from Fowler's book format; it is methodology, not an external compliance certificate.

<a id="ref-bloom"></a>
**Anderson, Lorin W., David R. Krathwohl, and collaborators.** *A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy of Educational Objectives*, abridged edition. Longman/Pearson, copyright 2001; publisher lists publication December 19, 2000. ISBN 9780801319037. [Original-edition publisher record](https://www.mypearsonstore.com/bookstore/taxonomy-for-learning-teaching-and-assessing-a-revision-080131903X); [later international edition](https://www.pearson.com/en-gb/subject-catalog/p/taxonomy-for-learning-teaching-and-assessing-a-pearson-new-international-edition/P200000003582/9781292042848). **University of Illinois Chicago.** “Bloom's Taxonomy of Educational Objectives,” undated [secondary teaching guide](https://teaching.uic.edu/cate-teaching-guides/syllabus-course-design/blooms-taxonomy-of-educational-objectives/). The revised framework includes cognitive processes and a knowledge dimension; a course's chosen activities are our application of it.

## Protocols, operations and implementation contracts

<a id="ref-jwt"></a>
**Jones, Michael B., John Bradley, and Nat Sakimura.** “JSON Web Token (JWT).” RFC 7519, May 2015. DOI: [10.17487/RFC7519](https://doi.org/10.17487/RFC7519). [RFC Editor publication](https://www.rfc-editor.org/rfc/rfc7519). Our signed token implementation still depends on current session and ownership checks.

<a id="ref-sse"></a>
**WHATWG.** *HTML Living Standard*, section 9.2, “Server-sent Events.” Living standard. [Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html). Provides framing and native EventSource processing; our Fetch client implements its own restricted reader.

<a id="ref-dns"></a>
**Mockapetris, Paul.** “Domain Names — Concepts and Facilities.” RFC 1034, November 1987. DOI: [10.17487/RFC1034](https://doi.org/10.17487/RFC1034). [RFC Editor publication](https://www.rfc-editor.org/rfc/rfc1034). Naming is distinct from TLS, routing and application deployment.

<a id="ref-sre"></a>
**Ewaschuk, Rob; edited by Betsy Beyer.** “Monitoring Distributed Systems,” chapter 6 in *Site Reliability Engineering*, Google/O'Reilly, 2016. [Original online chapter](https://sre.google/sre-book/monitoring-distributed-systems/). Used for service-oriented monitoring questions; our dashboard implements only a small subset.

<a id="ref-docker-limits"></a>
**Docker.** “Resource Constraints.” Living Docker Engine manual. [Official documentation](https://docs.docker.com/engine/containers/resource_constraints/). Ceilings, observed consumption and reserved capacity are different concepts.

<a id="ref-sqlalchemy"></a>
**SQLAlchemy project.** “Asynchronous I/O (asyncio).” Version 2.0 manual. [Versioned documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html). See “Using AsyncSession with Concurrent Tasks”; the installed version remains defined by `uv.lock`.

<a id="ref-alembic"></a>
**Alembic project.** “Auto Generating Migrations.” Living manual. [Official documentation](https://alembic.sqlalchemy.org/en/latest/autogenerate.html). Generated revisions are candidates requiring review, especially for renames and compatibility.

<a id="ref-backup"></a>
**PostgreSQL Global Development Group.** “Backup and Restore.” PostgreSQL 17 manual, chapter 25. [Versioned documentation](https://www.postgresql.org/docs/17/backup.html). Logical dumps, file-system backup and continuous archiving are separate approaches.

<a id="ref-outbox"></a>
**Richardson, Chris.** “Pattern: Transactional Outbox.” Undated author-maintained pattern account. [Original account](https://microservices.io/patterns/data/transactional-outbox.html). Describes database/outgoing-message coordination and the possibility of duplicate relay publication.

<a id="ref-resend-idempotency"></a>
**Resend.** “Idempotency Keys.” Living service documentation. [Official documentation](https://resend.com/docs/dashboard/emails/idempotency-keys). At access time the documented key retention window was 24 hours; this is not a universal exactly-once email guarantee.

<a id="ref-fernet"></a>
**PyCA cryptography project.** “Fernet (Symmetric Encryption).” Living manual. [Official documentation](https://cryptography.io/en/latest/fernet/). Authenticated encryption protects the pending payload under an operator-managed key; recovery/key-rotation obligations remain.

## How to use these readings

For a historical claim, identify what the source actually says, its authorship and its date. For an implementation claim, inspect the edition's code and executed evidence instead. A source's credibility does not establish that our code implements its idea. A figure, direct quotation or substantial third-party extract would need its own attribution/permission assessment before publication; none is added by this bibliography.
