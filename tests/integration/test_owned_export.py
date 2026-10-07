import json

from app.models import Conversation, Generation, Message
from tests.conftest import login, signup


async def test_export_allowlist_ownership_pages_and_abuse(client, application):
    assert (await client.get("/api/account/export")).status_code == 401
    owner = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    async with application.state.factory() as db:
        first = Message(conversation_id=cid, role="user", content="private-owned-prompt")
        db.add(first)
        db.add_all([Conversation(user_id=owner["id"], title=f"export-{i}") for i in range(101)])
        await db.flush()
        db.add(
            Generation(
                user_id=owner["id"],
                conversation_id=cid,
                request_key="export-fixture",
                message_id=first.id,
                reserved_units=1,
                expires_at=1,
                status="complete",
            )
        )
        await db.commit()
    responses = []
    for section in ("conversations", "messages", "runs"):
        response = await client.get("/api/account/export", params={"section": section})
        assert response.status_code == 200
        data = response.json()
        assert data["account"]["id"] == owner["id"] and data["format"] == "firehose360-owned-v1"
        responses.append(data)
    assert len(responses[0]["items"]) == 100 and responses[0]["next_cursor"]
    next_page = (
        await client.get("/api/account/export", params={"cursor": responses[0]["next_cursor"]})
    ).json()
    assert len(next_page["items"]) == 2 and next_page["next_cursor"] is None
    encoded = json.dumps(responses)
    assert "private-owned-prompt" in encoded
    for forbidden in (
        "password_hash",
        "refresh_tokens",
        "jwt_secret",
        "payload",
        "mfa_secret",
        "recovery_codes",
    ):
        assert forbidden not in encoded
    await login(client)
    assert (
        await client.get("/api/account/export", params={"cursor": responses[0]["next_cursor"]})
    ).status_code == 400
    assert (await client.get("/api/account/export?section=messages")).json()["items"] == []
    assert (await client.get("/api/account/export?section=unknown")).status_code == 422
    for _ in range(8):
        await client.get("/api/account/export")
    assert (await client.get("/api/account/export")).status_code == 429
