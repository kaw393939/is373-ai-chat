"""Native asyncio cancellation must persist observed text and release the lease."""

import asyncio

import pytest

from app.models import Generation, Message, User
from app.providers import TextDelta
from app.schemas import Prompt
from app.services import generate, prepare_run
from app.transport import encode_stream
from tests.conftest import signup


async def test_native_task_cancel_finalizes_stream(client, application):
    user = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    async with application.state.factory() as db:
        run, history, limit = await prepare_run(
            db,
            await db.get(User, user["id"]),
            cid,
            Prompt(content="held", request_key="native-cancellation"),
            application.state.config,
        )
    observed = asyncio.Event()

    class Held:
        async def stream(self, *args):
            yield TextDelta("synthetic partial")
            await asyncio.Event().wait()

    async def consume():
        async for frame in encode_stream(
            generate(application.state.factory, Held(), run, history, limit)
        ):
            if "event: delta" in frame:
                observed.set()

    task = asyncio.create_task(consume())
    await asyncio.wait_for(observed.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    async with application.state.factory() as db:
        saved = await db.get(Generation, run.id)
        message = await db.get(Message, run.message_id)
        assert saved.status == "cancelled" and message.content == "synthetic partial"


@pytest.mark.parametrize("event_name,expected", [("started", ""), ("delta", "synthetic partial")])
async def test_response_cancellation_while_sending_closes_generation(
    client, application, event_name, expected
):
    from app.transport import GenerationResponse

    user = await signup(client)
    cid = (await client.post("/api/conversations")).json()["id"]
    async with application.state.factory() as db:
        run, history, limit = await prepare_run(
            db,
            await db.get(User, user["id"]),
            cid,
            Prompt(content="held", request_key="backpressure-cancellation"),
            application.state.config,
        )
    observed = asyncio.Event()

    class Held:
        async def stream(self, *args):
            yield TextDelta("synthetic partial")
            await asyncio.Event().wait()

    async def send(message):
        if message[
            "type"
        ] == "http.response.body" and f"event: {event_name}".encode() in message.get("body", b""):
            observed.set()
            await asyncio.Event().wait()  # The generator is paused at its yield.

    response = GenerationResponse(
        encode_stream(generate(application.state.factory, Held(), run, history, limit))
    )
    task = asyncio.create_task(response.stream_response(send))
    await asyncio.wait_for(observed.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    async with application.state.factory() as db:
        saved = await db.get(Generation, run.id)
        message = await db.get(Message, run.message_id)
        assert saved.status == "cancelled" and message.content == expected
