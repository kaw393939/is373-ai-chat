import os
import subprocess
import sys

import httpx
import pytest
from sqlalchemy import delete

from app.config import Settings
from app.main import create_app
from app.models import Base, RoleBudget, User
from app.security import hash_password

PASSWORD = "correct-horse-workshop-123"


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch):
    # Local credentials/provider choices must never influence mock test fixtures.
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for field in Settings.model_fields:
        monkeypatch.delenv(field.upper(), raising=False)


@pytest.fixture
async def application(tmp_path):
    url = os.environ.get("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db")
    env = {**os.environ, "DATABASE_URL": url, "APP_ENV": "development"}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, check=True)
    assets = tmp_path / "dist"
    (assets / "assets").mkdir(parents=True)
    (assets / "index.html").write_text('<html lang="en">Workshop</html>')
    config = Settings(
        database_url=url,
        registration_policy="open",
        static_dir=str(assets),
        metrics_path=str(tmp_path / "metrics.json"),
    )
    app = create_app(config)
    async with app.state.factory() as db:
        for table in reversed(Base.metadata.sorted_tables):
            await db.execute(delete(table))
        db.add_all([RoleBudget(role="user"), RoleBudget(role="admin")])
        db.add(
            User(
                email="admin@example.org",
                password_hash=hash_password(PASSWORD),
                role="admin",
                approved=True,
            )
        )
        await db.commit()
    yield app
    await app.state.engine.dispose()


@pytest.fixture
async def client(application):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:8000"},
    ) as c:
        yield c


async def login(client, email="admin@example.org", password=PASSWORD):
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.headers["Authorization"] = "Bearer " + token
    return response.json()["user"]


async def signup(client, email="student@example.org"):
    r = await client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text
    return await login(client, email)
