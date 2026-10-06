# Browser review and security findings

October 6, 2026. Target: firehose360.com and isolated local/CI fixtures. This is a targeted application review, not an exhaustive penetration test.

## Feature notes

| Feature | Evidence and resulting change |
|---|---|
| Registration / login | Computer Use registered an ordinary review account; login was refused before approval and succeeded after admin approval. |
| Streaming | The new account received a real provider response. Literal HTML attack text stayed text. |
| Roles / limits / dashboard | Ordinary user had no admin navigation. Admin loaded accounts, budgets and live metrics. Corrected the loading message and static connection label. |
| History / rename / delete | Python Playwright exercised persistence, rename, retry and deletion. Native rename prompts did not open in the in-app browser; replaced them with app dialogs and verified title saving on the deployed release. |
| Mobile | History/search were hidden by CSS. Restored them and added a 390-pixel browser journey plus keyboard sending. |
| Reply display / failure | Added safe Markdown, copy buttons, retained drafts after rejected admission, and replaced indefinite empty “Thinking” messages. Remote Markdown images are omitted; unsafe URL schemes are filtered. |
| Email | Verification, recovery, approval notification and encrypted outbox implemented and integration-tested. Production delivery still requires Resend login/key/domain activation and inbox proof. |

## Security changes and checks

- Password changes now require current-password verification. Hashing runs in bounded worker threads, with two concurrent operations. Login has IP and account throttles.
- Request bodies are bounded to 64 KiB, including chunked bodies. HTTP concurrency is capped. Validation errors omit submitted inputs, including passwords. Default access logs are disabled; structured logs exclude query values.
- Host headers are restricted. Production has HTTPS, HSTS, CSP, frame denial, MIME protection, no-store API responses and Secure/HttpOnly/Strict refresh cookies. Foreign-origin refresh/login attempts are rejected.
- Ownership checks protect read/rename/delete/stream/cancel operations. Role checks protect administration. Parameterized ORM queries and constrained schemas prevent SQL injection and role assignment through registration.
- JWT validation fixes algorithm, issuer, audience and required claims. Refresh reuse revokes the family. Password/reset/admin revocation cancels active generations and invalidates sessions.
- Recovery and verification links are purpose-bound, hashed, expiring and single-use. A PostgreSQL race test confirms only one sibling link can be redeemed. Recovery requests are generic and rate-limited; sending quotas, bounded retries and provider idempotency constrain abuse.
- Browser rendering tests include script tags, Markdown JavaScript URLs and external tracking images. Markdown uses React nodes without raw-HTML plugins. External links have no opener/referrer; remote images cannot silently leak browser data.
- Probes for .env, .git, API documentation and traversal return 404. Missing credentials return 401; ordinary accounts receive 403 on admin access. Tampered/expired/revoked JWTs are covered.
- The first review release was blocked by two fixable HIGH cryptography advisories (CVE-2026-69247/69249). Updated the locked dependency from 48.0.1 to 50.0.2; the final image passed the unchanged gate. [Upstream release notes](https://cryptography.io/en/latest/changelog/).
- npm audit found no known frontend advisories at review time; CI now gates HIGH/CRITICAL frontend advisories. The image gate/SBOM continue to report unfixed OS advisories explicitly.

## Follow-up ideas and limits

Useful next features: administrator MFA/passkeys, session/device listing, conversation export and pagination, historical resource graphs/alerts, off-host backups, attachment/RAG/tool workflows and cross-tab refresh coordination. These are separate product extensions. The single-server deployment and unfixed Debian advisories remain operational constraints. Provider answers require checking: a real response incorrectly connected current-password verification with injection prevention, illustrating why model output is never an authorization or security decision.

Sources: [OWASP authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), [OWASP recovery](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html), [React Markdown security](https://github.com/remarkjs/react-markdown#security).
