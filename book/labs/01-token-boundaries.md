# Lab 01: a valid token is only part of an authorization decision

## Problem and objectives

A developer says, “The JWT is signed, so the request is secure.” Investigate what the signature actually establishes and which decisions still require current account/session and ownership data. By the end, explain readable claims versus encrypted data, demonstrate an expiry failure, and trace authorization to a conversation.

Bloom emphasis: **understand, apply, analyze**. Your observable artifacts are an expiry counterexample, an annotated authorization trace and a comparison of two session designs. Complete the common [laboratory preflight](README.md); prior knowledge is Python function calls, exceptions and HTTP status codes.

Read [identity](../04-auth.md), [code-reading guidance](../00-reading-code.md) and the Liskov/Beck discussions in [engineering ideas](../13-engineering-ideas.md). Canonical requirements: [REQ-IDENTITY](../../docs/project/baseline.md#req-identity) and [REQ-LEARNING](../../docs/project/baseline.md#req-learning). The code/tests are linked rather than copied into a second application.

## Environment and prerequisites

Use a learner-owned local checkout, locked Python dependencies (`uv sync --frozen`) and a terminal in the repository root. This exercise uses synthetic identifiers and a lab-only signing key; it makes no HTTP request and connects to no database. Never substitute a real token or secret. No provider credential or Docker service is required for this pilot.

## Guided investigation and controlled failure

Read `access_token` and `decode_token` in [security.py](../../app/security.py). Identify `sub`, `sid`, `iss`, `aud`, `iat` and `exp`. Explain why the permitted signing algorithm comes from server code, not an untrusted token header.

Run this controlled expiry experiment:

```sh
uv run python - <<'PY'
from datetime import datetime, timedelta, timezone
import os
import jwt
from fastapi import HTTPException
from app.config import Settings
from app.security import decode_token

# A child-process experiment must not inherit unrelated app configuration.
for field in Settings.model_fields:
    os.environ.pop(field.upper(), None)
config = Settings(
    _env_file=None,
    app_env="development",
    base_url="http://lab.invalid",
    jwt_secret="lab-only-signing-key-do-not-deploy-0000000000000000",
    provider="mock",
    email_provider="disabled",
)
instant = datetime.now(timezone.utc)
claims = dict(sub="synthetic-user", sid="synthetic-family",
              iss=config.base_url, aud="373-chat", iat=instant,
              exp=instant - timedelta(seconds=1))
token = jwt.encode(claims, config.jwt_secret, algorithm="HS256")

# Deliberately incomplete validation for comparison, never an app repair.
unchecked = jwt.decode(token, config.jwt_secret, algorithms=["HS256"],
                       issuer=config.base_url, audience="373-chat",
                       options={"verify_exp": False})
assert unchecked["sub"] == "synthetic-user"
try:
    decode_token(token, config)
except HTTPException as failure:
    assert failure.status_code == 401
    print("Expected: incomplete validation accepted expiry; app rejected it.")
else:
    raise AssertionError("Expired token was accepted")
PY
```

This intentionally shows a bad validation choice without modifying the running application. A correct signature can coexist with an expired claim. There is no repair to deploy: the app already rejects this case. The “repair” is explaining and retaining the full validation contract rather than weakening it.

Now trace the `current` dependency in [main.py](../../app/main.py), `rotate` and `owned` in [services.py](../../app/services.py), and the corresponding [account](../../tests/integration/test_accounts.py) and [cross-account](../../tests/integration/test_web_security.py) tests. These are a code-reading extension, not permission to run destructive database tests against a shared environment.

## Acceptance evidence

Submit the experiment's expected output, the source commit, and a short explanation of each step: signed claims → current account/session checks → conversation ownership → allowed action. Explain what happens when an account becomes inactive, a family is revoked, or another user guesses a conversation ID. Cite the exact functions/tests you inspected.

An instructor should ask a counterexample: this app's JWT has no role claim; if a designer added one, would it replace current server-side permission checks? Would hiding a UI button establish permission? Identify which check owns the answer. Assess understanding of boundaries rather than a screenshot of a passing script alone. Use the [shared rubric](../instructor/README.md) for evidence, reasoning and justified alternatives.

## Reflection and extension

Compare this hybrid token/session design with an opaque server-session cookie. Name one advantage and one operating cost of each. Explain why SHA-256 digests of random refresh tokens and Argon2 password hashes have different purposes.

Optional: in a disposable local branch, add tests for a wrong issuer, wrong audience and missing required claim. Keep credentials synthetic, and review your diff before committing. Do not loosen the production decoder to make a test pass.

## Troubleshooting, cleanup and status

If imports fail, repeat frozen preflight. If the expected rejection is absent, inspect `exp` and the decoder contract; do not disable expiry validation. This child-process experiment creates no database/service and changes no parent-shell configuration, so no service cleanup is needed. Keep synthetic evidence only. The command was independently rerun by a maintainer agent during this review; learner time, accessibility of the instructions and independent human second-reader success remain pending. This pilot does not prove the entire authentication system or replace the integration/browser suites.
