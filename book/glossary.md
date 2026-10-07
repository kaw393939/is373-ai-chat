# Glossary: distinctions that change decisions

These definitions describe how terms are used in this book. Follow the linked chapter for a worked example and the [references](references.md) for original specifications. An unfamiliar term should be defined on first meaningful use as well as here.

## Requests, identity and user experience

| Term | Meaning in this system | Common confusion |
|---|---|---|
| Authentication | Establishing which account/session presented a request | A valid identity does not grant every action |
| Authorization | Deciding whether that current account may perform that operation on that object | Hiding a button is not server authorization |
| JWT | JSON Web Token: a compact claims format; this app signs access claims | Signing does not encrypt the readable payload; not every JWT is only a signed token |
| Access token | Short-lived bearer credential supplied in the Authorization header | It still undergoes current account/family checks here |
| Refresh token | Random bearer secret used to obtain another access token | It is opaque here, not another JWT |
| Session family | Durable group of related rotating refresh tokens | Revoking a family differs from ending one browser request |
| Issuer / audience | Expected token source / intended recipient of its claims | A signature with an accepted key alone is insufficient validation |
| Origin | Browser scheme, host and port | Sharing a domain suffix does not make two origins identical |
| HttpOnly / Secure / SameSite | Cookie controls for script access, HTTPS transport and cross-site sending | No single attribute proves complete CSRF protection |
| CSRF | Cross-site request forgery: abusing ambient browser credentials for an unwanted action | Bearer-token and cookie-authenticated endpoints need different reasoning |
| XSS | Cross-site scripting: executing attacker-controlled script in a trusted page | Escaping one field does not validate every rendering path |
| SSE | Server-sent events: UTF-8 text frames separated by protocol delimiters | A network chunk is not necessarily one frame |
| EOF | End of a byte/text stream | Transport end does not prove a model emitted successful completion |
| Accessibility | Usability by people with varied abilities and interaction methods | Automated checks or a mobile screenshot alone are incomplete evidence |
| REST / HATEOAS | Fielding's architectural constraints / hypermedia guiding available state transitions | JSON over HTTP, or adding a `links` field, does not alone establish REST |

## Data, architecture and accounting

| Term | Meaning in this system | Common confusion |
|---|---|---|
| ORM | Object-relational mapping: translating between application objects and relational data | It does not eliminate SQL, constraints or transaction design |
| Transaction | A database consistency boundary ending in commit or rollback | It need not span the whole HTTP request or external stream |
| Migration | Versioned change to schema/data interpretation | Autogeneration is a proposal; downgrade is not a backup |
| Unit of work | Coordination of persistence changes within a consistency boundary | Another repository wrapper is not automatically necessary |
| Adapter / port | Translation of an external mechanism / boundary expected by application code | Similar method names do not prove behavioral substitution |
| Invariant | A condition that the design intends to preserve | A comment or test name is not proof that it always holds |
| Idempotency key | Stable request identity used to detect repeated effects | Scope, payload and retention window bound the guarantee |
| Outbox | Durable outgoing message committed with business data and delivered afterward | A relay may retry; the pattern alone does not supply exactly-once delivery |
| Reservation units | Conservative admission allowance from input bytes plus maximum output tokens | They are neither exact provider tokens nor billed dollars |
| Capability | Explicitly supported behavior of an adapter or API | Text streaming does not imply tool/image/retrieval parity |
| SOLID | Single responsibility, open/closed, Liskov substitution, interface segregation and dependency inversion | They guide tradeoffs; counting classes or patterns does not demonstrate them |
| Technical debt | Cost of postponing consolidation of an evolving design/understanding | Not every defect or unpopular style choice is debt |

## Delivery and operation

| Term | Meaning in this system | Common confusion |
|---|---|---|
| Container image / container | Packaged application filesystem/configuration / running instance | Neither is an independent physical machine |
| Digest / tag / commit SHA | Image-content identity / convenient registry name / source-history identity | Equal commits do not establish equal rebuilt image bytes; tags can move |
| Release | Selected artifact plus runtime configuration and compatible schema | Uploading an image is not verified deployment |
| CI | Continuous integration: frequent integration with feedback | A workflow file alone does not establish the team practice |
| Continuous delivery / deployment | Maintaining deployability / automatically releasing accepted changes | Delivery does not require publishing every commit to users |
| Environment | Independently configured deployment/data/effect boundary | A new DNS name alone does not create one; shared hosts retain shared risks |
| SemVer | Semantic Versioning: version meaning tied to an explicitly defined public contract | A package version `1.0.0` alone does not establish a release policy |
| Twelve-factor | Wiggins's service-application design methodology | An `.env` file or Docker image is not compliance certification |
| CPU / PID limit | Processor-time allowance / bound on process identifiers used by a container | A PID limit controls process count, not total memory |
| SRE | Site reliability engineering: applying engineering to service operation and reliability | A dashboard alone does not establish an SRE practice |
| GHCR | GitHub Container Registry: hosting for packaged images/artifacts | Registry publication is separate from deployment |
| Resource ceiling / usage | Configured maximum / observed consumption | A ceiling does not reserve dedicated capacity |
| Readiness / user journey | Current ability to serve a defined check / observed end-to-end user behavior | A database-ready response does not prove real provider or email availability |
| RPO / RTO | Recovery point/time objectives: tolerated data loss / restoration delay | A backup schedule and a successful dump do not prove either objective |
| SPF / DKIM / DMARC | Sender authorization / message signing / domain alignment and policy | An API success or DNS record alone does not prove inbox placement |
| SBOM | Software bill of materials listing components | It is neither a vulnerability report nor proof of safety |
| Coverage | Fraction of a specified code set executed by tests, accounting for exclusions | 100% measured Python execution is not 100% system correctness |
| Bloom-based objective | Assessed cognitive task such as analysis, evaluation or creation | Running commands once does not establish strategic judgment |
| Acceptance evidence | Observations that support a specific requirement within stated limits | A checked issue box or fluent explanation alone is insufficient |
