"""Test-only factory, mounted into CI's release image rather than shipped in it."""

import os

from app.config import Settings
from app.main import create_app as application
from tests.targets import browser_url, disposable_database


def create_app():
    token = os.environ["E2E_TARGET_TOKEN"]
    url = browser_url(os.environ["E2E_URL"])
    database = disposable_database(
        os.environ["DATABASE_URL"],
        os.environ.get("E2E_TEMP_ROOT"),
        os.environ.get("TEST_ALLOW_RESET"),
    )
    # Explicit values plus clearing environment fields prevent real integrations.
    for name in Settings.model_fields:
        os.environ.pop(name.upper(), None)
    config = Settings(
        _env_file=None,
        database_url=database,
        base_url=url,
        app_env="development",
        jwt_secret="synthetic-browser-lab-secret-with-no-production-authority",
        provider="mock",
        email_provider="disabled",
        # Public synthetic fixture value; no enrolled production factor uses it.
        mfa_encryption_key="c3ludGhldGljLWJyb3dzZXItbGFiLWtleS1vbmx5ISE=",
        static_dir=os.environ.get("E2E_STATIC_DIR", "frontend/dist"),
        commit_sha=os.environ.get("E2E_COMMIT_SHA", "browser-lab"),
    )
    app = application(config)

    @app.get("/_workshop/identity")
    async def identity():
        return {"token": token, "provider": "mock", "email": "disabled", "disposable": True}

    return app
