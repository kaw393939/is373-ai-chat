import asyncio

import httpx
import pytest
from fastapi import Depends
from sqlalchemy import func, select

from app.models import User
from tests.conftest import login, signup


async def test_two_preauthenticated_admin_requests_preserve_eligible_admin(client, application):
    if application.state.engine.dialect.name != "postgresql":
        pytest.skip("Requires real PostgreSQL transaction/lock semantics")
    first = await login(client)
    first_token = client.headers["Authorization"]
    second = await signup(client, "second-admin@example.org")
    second_token = client.headers["Authorization"]
    async with application.state.factory() as db:
        user = await db.get(User, second["id"])
        user.role = "admin"
        await db.commit()
    route = next(
        route
        for route in application.routes
        if getattr(route, "path", None) == "/api/admin/users/{uid}"
    )
    admin_dependency = next(dep.call for dep in route.dependant.dependencies if dep.name == "actor")
    current_dependency = next(
        dep.call
        for dep in next(
            dep for dep in route.dependant.dependencies if dep.name == "actor"
        ).dependencies
        if dep.name == "user"
    )
    barrier = asyncio.Barrier(2)

    async def authenticated_at_same_time(user=Depends(current_dependency)):
        actor = await admin_dependency(user)
        await barrier.wait()
        return actor

    application.dependency_overrides[admin_dependency] = authenticated_at_same_time
    change = {"role": "user", "active": False, "approved": False}
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application), base_url="http://localhost:8000"
        ) as peer:
            peer.headers["Authorization"] = first_token
            client.headers["Authorization"] = second_token
            outcomes = await asyncio.gather(
                peer.patch(f"/api/admin/users/{second['id']}", json=change),
                client.patch(f"/api/admin/users/{first['id']}", json=change),
            )
    finally:
        application.dependency_overrides.pop(admin_dependency)
    assert sorted(response.status_code for response in outcomes) == [200, 403]
    async with application.state.factory() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(User)
                .where(
                    User.role == "admin",
                    User.active.is_(True),
                    User.approved.is_(True),
                    User.email_verified.is_(True),
                )
            )
            == 1
        )
