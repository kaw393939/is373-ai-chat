import pytest

from app.models import Message, User
from app.providers import StreamEnd, TextDelta
from app.schemas import Prompt
from app.services import generate, prepare_run
from tests.conftest import signup


@pytest.mark.parametrize(
    "events,expected",
    [
        ([], "failed"),
        ([TextDelta("partial")], "failed"),
        ([TextDelta("partial"), StreamEnd("incomplete")], "incomplete"),
        ([StreamEnd("refused")], "refused"),
        ([StreamEnd("complete"), TextDelta("late")], "failed"),
        ([{"text": "invalid old contract"}], "failed"),
    ],
)
async def test_terminal_state_preserves_partial_text(client, application, events, expected):
    user = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    async with application.state.factory() as db:
        run, history, limit = await prepare_run(
            db,
            await db.get(User, user["id"]),
            cid,
            Prompt(content="synthetic", request_key="terminal-fixture"),
            application.state.config,
        )

    class Fake:
        async def stream(self, *args):
            for item in events:
                yield item

    output = [
        event async for event in generate(application.state.factory, Fake(), run, history, limit)
    ]
    assert output[-1].status == expected
    async with application.state.factory() as db:
        saved = await db.get(Message, run.message_id)
        assert saved.content == ("partial" if events and events[0] == TextDelta("partial") else "")
    if expected == "failed":
        assert any(event.kind == "error" for event in output)
