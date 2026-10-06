from argparse import Namespace

from sqlalchemy import select

from app.cli import execute
from app.config import Settings
from app.main import create_app
from app.models import User
from tests.conftest import PASSWORD


async def test_seed_and_admin_bootstrap(application, monkeypatch):
    monkeypatch.setattr("app.cli.Settings", lambda: application.state.config)
    monkeypatch.setenv("ADMIN_PASSWORD", PASSWORD)
    await execute(Namespace(command="seed"))
    await execute(Namespace(command="admin", email="second-admin@example.org"))
    await execute(Namespace(command="admin", email="second-admin@example.org"))
    await execute(Namespace(command="prune"))
    async with application.state.factory() as db:
        user = await db.scalar(select(User).where(User.email == "second-admin@example.org"))
        assert user.role == "admin" and user.approved


async def test_headless_client_without_origin(client):
    client.headers.pop("Origin")
    r = await client.post(
        "/api/auth/login", json={"email": "admin@example.org", "password": PASSWORD}
    )
    assert r.status_code == 200


def test_api_only_asset_path(tmp_path):
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{tmp_path}/none.db",
            static_dir=str(tmp_path / "absent"),
        )
    )
    assert not any(getattr(r, "path", None) == "/assets" for r in app.routes)
