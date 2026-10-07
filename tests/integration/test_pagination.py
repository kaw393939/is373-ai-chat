import pytest

from app.models import Conversation, Generation, Message, User
from tests.conftest import PASSWORD, login, signup


async def collect(client, path):
    rows, cursor = [], None
    while True:
        response = await client.get(
            path, params={"page": "true", "limit": 37, **({"cursor": cursor} if cursor else {})}
        )
        assert response.status_code == 200, response.text
        page = response.json()
        assert len(page["items"]) <= 37
        rows.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            return rows


async def test_large_owned_list_and_server_search(client, application):
    owner = await signup(client)
    admin = await login(client)
    async with application.state.factory() as db:
        db.add_all(
            [
                Conversation(user_id=owner["id"], title=f"lesson-{i}", created_at=10)
                for i in range(310)
            ]
        )
        db.add(Conversation(user_id=owner["id"], title="old needle-%_", created_at=1))
        db.add(Conversation(user_id=admin["id"], title="foreign needle-%_", created_at=0))
        await db.commit()
    await login(client, owner["email"])
    rows = await collect(client, "/api/conversations")
    assert len(rows) == 311 and len({row["id"] for row in rows}) == 311
    result = (
        await client.get("/api/conversations", params={"page": "true", "q": "needle-%_"})
    ).json()
    assert [row["title"] for row in result["items"]] == ["old needle-%_"]
    first = (await client.get("/api/conversations?page=true&limit=1")).json()
    assert (
        await client.get(
            "/api/conversations",
            params={"page": "true", "cursor": first["next_cursor"], "q": "changed"},
        )
    ).status_code == 400
    await login(client)
    assert (
        await client.get(
            "/api/conversations", params={"page": "true", "cursor": first["next_cursor"]}
        )
    ).status_code == 400
    assert (await client.get("/api/conversations?page=true&limit=101")).status_code == 422
    assert isinstance((await client.get("/api/conversations")).json(), list)


async def test_older_admin_accounts_and_bounded_history(client, application):
    owner = await login(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    async with application.state.factory() as db:
        db.add_all(
            [
                User(email=f"older-{i}@example.org", password_hash=PASSWORD, created_at=1)
                for i in range(260)
            ]
        )
        messages = [
            Message(conversation_id=cid, role="assistant", content=str(i), created_at=1)
            for i in range(135)
        ]
        db.add_all(messages)
        await db.flush()
        db.add_all(
            [
                Generation(
                    user_id=owner["id"],
                    conversation_id=cid,
                    message_id=message.id,
                    request_key=f"fixture-{i}",
                    reserved_units=1,
                    status="complete",
                    expires_at=1,
                    created_at=1,
                )
                for i, message in enumerate(messages)
            ]
        )
        await db.commit()
    users = await collect(client, "/api/admin/users")
    assert len(users) == 261 and len({row["id"] for row in users}) == 261
    found = (await client.get("/api/admin/users?page=true&q=older-259@")).json()
    assert found["items"][0]["email"] == "older-259@example.org"
    assert isinstance((await client.get("/api/admin/users")).json(), list)
    summary = (await client.get(f"/api/conversations/{cid}")).json()
    assert len(summary["messages"]) == len(summary["runs"]) == 50
    assert summary["messages_cursor"] and summary["runs_cursor"]
    for kind in ("messages", "runs"):
        rows = await collect(client, f"/api/conversations/{cid}/{kind}")
        assert len(rows) == 135 and len({row["id"] for row in rows}) == 135
        chunks = [rows[i : i + 37] for i in range(0, len(rows), 37)]
        assert all(
            [row["id"] for row in chunk] == sorted(row["id"] for row in chunk) for chunk in chunks
        )
    await signup(client, "outsider@example.org")
    for kind in ("messages", "runs"):
        assert (await client.get(f"/api/conversations/{cid}/{kind}")).status_code == 404
    assert (await client.get("/api/admin/users?page=true")).status_code == 403


@pytest.mark.parametrize("cursor", ["bad", "a.b", ".", "a.b.c"])
async def test_invalid_cursors(client, cursor):
    await signup(client)
    assert (
        await client.get("/api/conversations", params={"page": "true", "cursor": cursor})
    ).status_code == 400
