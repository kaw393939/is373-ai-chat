from sqlalchemy import select

from app.models import Generation, Message, RoleBudget, User, now
from app.providers import MockProvider, TextDelta
from app.schemas import Prompt
from app.services import generate, prepare_run
from tests.conftest import login, signup


def prompt(text="Explain dependency inversion", key="request-first"):
    return {"content": text, "request_key": key, "model": "default"}


async def test_owned_chat_stream_history_rename_delete(client):
    first = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    assert len((await client.get("/api/conversations")).json()) == 1
    response = await client.post(f"/api/conversations/{cid}/stream", json=prompt())
    assert response.status_code == 200
    assert "event: started" in response.text and "event: completed" in response.text
    assert "Workshop" in response.text and "Explain" in response.text
    assert (await client.post(f"/api/conversations/{cid}/stream", json=prompt())).status_code == 409
    data = (await client.get(f"/api/conversations/{cid}")).json()
    assert len(data["messages"]) == 2 and data["runs"][0]["status"] == "complete"
    rid = data["runs"][0]["id"]
    assert (await client.post(f"/api/generations/{rid}/cancel")).status_code == 204
    assert (
        await client.patch(f"/api/conversations/{cid}", json={"title": "My lesson"})
    ).status_code == 200
    await login(client)
    for method, path in [
        ("get", f"/api/conversations/{cid}"),
        ("delete", f"/api/conversations/{cid}"),
        ("post", f"/api/generations/{rid}/cancel"),
    ]:
        assert (await getattr(client, method)(path)).status_code == 404
    assert (await client.post("/api/generations/missing/cancel")).status_code == 404
    await login(client, first["email"])
    assert (await client.delete(f"/api/conversations/{cid}")).status_code == 204
    assert (await client.get(f"/api/conversations/{cid}")).status_code == 404


async def test_budget_and_model_enforcement(client, application):
    await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    bad = prompt()
    bad["model"] = "unknown"
    assert (await client.post(f"/api/conversations/{cid}/stream", json=bad)).status_code == 403
    async with application.state.factory() as db:
        budget = await db.get(RoleBudget, "user")
        budget.model_enabled = False
        await db.commit()
    assert (await client.post(f"/api/conversations/{cid}/stream", json=prompt())).status_code == 403
    async with application.state.factory() as db:
        budget = await db.get(RoleBudget, "user")
        budget.model_enabled = True
        budget.daily_requests = 1
        await db.commit()
    assert (await client.post(f"/api/conversations/{cid}/stream", json=prompt())).status_code == 200
    assert (
        await client.post(f"/api/conversations/{cid}/stream", json=prompt(key="second-request"))
    ).status_code == 429


async def test_context_units_and_active_limits(client, application):
    user = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    async with application.state.factory() as db:
        db.add(Message(conversation_id=cid, role="user", content="x" * 33000))
        await db.commit()
    assert (await client.post(f"/api/conversations/{cid}/stream", json=prompt())).status_code == 413
    async with application.state.factory() as db:
        item = await db.scalar(select(Message))
        item.content = "small"
        budget = await db.get(RoleBudget, "user")
        budget.daily_units = 100
        await db.commit()
    assert (await client.post(f"/api/conversations/{cid}/stream", json=prompt())).status_code == 429
    async with application.state.factory() as db:
        budget = await db.get(RoleBudget, "user")
        budget.daily_units = 100000
        await db.commit()
        current = await db.get(User, user["id"])
        run, history, limit = await prepare_run(
            db, current, cid, Prompt(**prompt()), application.state.config
        )
    assert (
        await client.post(f"/api/conversations/{cid}/stream", json=prompt(key="second-request"))
    ).status_code == 429
    assert (await client.delete(f"/api/conversations/{cid}")).status_code == 409
    async with application.state.factory() as db:
        current = await db.get(Generation, run.id)
        current.expires_at = now() - 1
        await db.commit()
    assert (
        await client.post(f"/api/conversations/{cid}/stream", json=prompt(key="new-request"))
    ).status_code == 200


async def test_cancel_and_provider_failure_preserve_state(client, application):
    user = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    async with application.state.factory() as db:
        current = await db.get(User, user["id"])
        run, history, limit = await prepare_run(
            db, current, cid, Prompt(**prompt()), application.state.config
        )
        run.cancel_requested = True
        db.add(run)
        await db.commit()
    events = [
        e async for e in generate(application.state.factory, MockProvider(), run, history, limit)
    ]
    assert "cancelled" in events[-1]

    class Broken:
        async def stream(self, *args):
            yield TextDelta("x" * 10000)

    async with application.state.factory() as db:
        run, history, limit = await prepare_run(
            db,
            await db.get(User, user["id"]),
            cid,
            Prompt(**prompt(key="broken-request")),
            application.state.config,
        )
    events = [e async for e in generate(application.state.factory, Broken(), run, history, limit)]
    assert "Provider unavailable" in "".join(events) and "failed" in events[-1]


async def test_parallel_admission_is_atomic(client, application):
    import asyncio

    import pytest
    from fastapi import HTTPException

    if application.state.engine.dialect.name != "postgresql":
        pytest.skip("PostgreSQL row-lock semantics; exercised in CI and server verification")
    user = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]

    async def admit(key):
        async with application.state.factory() as db:
            current = await db.get(User, user["id"])
            try:
                result = await prepare_run(
                    db, current, cid, Prompt(**prompt(key=key)), application.state.config
                )
                return result[0].id
            except HTTPException as e:
                return e.status_code

    outcomes = await asyncio.gather(admit("parallel-one"), admit("parallel-two"))
    assert outcomes.count(429) == 1 and sum(isinstance(x, str) for x in outcomes) == 1
