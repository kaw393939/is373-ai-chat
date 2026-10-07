"""Every browser module must identify the disposable mock target before use."""

import os

import pytest

from tests.targets import verify_browser_target


@pytest.fixture(scope="session", autouse=True)
def require_disposable_browser():
    verify_browser_target(
        os.environ.get("E2E_URL", "http://localhost:9001"),
        os.environ.get("E2E_TARGET_TOKEN"),
    )
