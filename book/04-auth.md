# 4 · Authentication is a lifecycle

[Security helpers](../app/security.py) hash passwords with Argon2id and sign access JWTs. Validation fixes algorithm, issuer and audience, and requires expiration/identity claims. A JWT is signed data, not encrypted storage: put no secrets inside it.

A successful login creates a database session family and a random refresh token. Only the token hash is stored. The JWT identifies the user and family. Each authenticated request also checks current user/session state, so disablement and revocation take effect immediately.

Refresh consumes its old token and creates a replacement. PostgreSQL locks the family during rotation. Reusing an already consumed token revokes that family. The frontend serializes refresh requests so concurrent UI calls do not accidentally rotate the same token twice.

Cookies are Secure in production, HttpOnly, SameSite=Strict, and scoped to `/api/auth`. Refresh/logout require the configured Origin. No CORS is needed for the same-origin deployment. Password changes revoke all sessions.

Authorization is separate: every conversation operation checks ownership; admin routes check the current role. Registration cannot set a role. Admin edits cannot remove the editing admin's own access. Administrative changes create audit events without recording passwords/tokens.

The initial enrollment policy is admin approval. Recovery links are issued by admins, expire after 30 minutes, are single-use and stored hashed. Links use a URL fragment so their tokens are not sent in ordinary HTTP request paths/access logs. Share them privately. Automated email is not configured in this release.

**Exercise:** revoke a session and try its still-unexpired JWT. Then use a refresh token twice and explain why the second attempt invalidates the family.
