# Primary references and discussion decisions

> Initial research record. See the [textbook](../README.md) and [implementation evidence](implementation-evidence.md) for current behavior.


Documentation reviewed October 6, 2026. Exact versions, pricing, provider capabilities, and platform restrictions must be rechecked when implementation begins.

## Sources

- [FastAPI authentication with JWT and password hashing](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [SQLAlchemy current async documentation](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html)
- [Alembic autogeneration and schema drift checks](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Docker installation on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Compose production configuration](https://docs.docker.com/compose/how-tos/production/)
- [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub deployment environment requirements and plan restrictions](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [GitHub Container Registry authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [DigitalOcean firewall](https://docs.digitalocean.com/products/networking/firewalls/), [monitoring](https://docs.digitalocean.com/products/monitoring/), and [backups](https://docs.digitalocean.com/products/backups/details/features/)
- [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) and [browser storage](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)
- [MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events), [streams](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams), and [WebAssembly](https://developer.mozilla.org/en-US/docs/WebAssembly/Guides/Concepts)
- [React](https://react.dev/learn), [Svelte](https://svelte.dev/docs/svelte/overview), and [Lit](https://lit.dev/docs/)
- [LiteLLM provider coverage](https://docs.litellm.ai/docs/providers) and [async streaming](https://docs.litellm.ai/docs/completion/stream)
- [Twelve-factor methodology](https://12factor.net/)

## Decisions to discuss

| Decision | Recommendation | Alternatives / implications |
|---|---|---|
| Frontend | React + TypeScript + Vite for course continuity | Svelte for compact reactivity; native Web Components for browser-first teaching |
| Backend | FastAPI + supported SQLAlchemy modern ORM + Alembic + PostgreSQL | Exact versions locked after compatibility checks |
| Provider integration | Own narrow contract; evaluate LiteLLM as one adapter | Direct SDKs for tighter control and smaller provider set |
| Initial models/providers | Choose two hosted providers | Capability/cost/privacy comparison after shortlist |
| Registry | GHCR | Docker Hub for continuity with calculator lessons |
| Deployment | Explicit Actions-driven migration/deploy/verify | Pull-based deployment controller if inbound SSH constraints justify it |
| Domain | Candidate chat.mywebclass.org already resolves to host | Confirm chosen route; application and TLS not yet created |
| Environments | Local + isolated CI + production initially | Separate staging droplet/DB when budget permits; same-host staging needs resource evaluation |
| Registration | Verified-email signup for classroom use | Invite-only or admin-approved enrollment |
| Admin transcript access | Metadata/usage by default | Explicit restricted transcript access only after privacy decision |
| Hosting capacity | Small hosted-LLM lab on existing host, after measurement | Increase RAM/managed DB for sustained production load |
| Repository visibility | Created private for discussion | Publish teaching material after visibility decision and sensitive-config review |

The first discussion should settle frontend direction and what “full featured” means for the initial release. The baseline includes complete account management, roles/admin, owned chat history, model selection, streaming/cancellation, and usage limits. Tools, document retrieval, uploads, collaboration, voice, and payments materially expand the project.
