"""An allow-listed owned-data export: authentication/outbox secrets never serialize."""

from sqlalchemy import select

from app.models import Conversation, Generation, Message
from app.pagination import page_rows

FIELDS = {
    "conversations": (Conversation, ("id", "title", "created_at")),
    "messages": (Message, ("id", "conversation_id", "role", "content", "created_at")),
    "runs": (
        Generation,
        ("id", "conversation_id", "status", "reserved_units", "actual_tokens", "created_at"),
    ),
}


async def owned_export(db, owner, section, limit, cursor, secret):
    model, fields = FIELDS[section]
    statement = select(model)
    if model is Message:
        statement = statement.join(Conversation).where(Conversation.user_id == owner.id)
    else:
        statement = statement.where(model.user_id == owner.id)
    items, next_cursor = await page_rows(
        db, model, statement, limit, cursor, f"export:{owner.id}:{section}", secret
    )
    return {
        "format": "firehose360-owned-v1",
        "section": section,
        "items": [{field: getattr(item, field) for field in fields} for item in items],
        "next_cursor": next_cursor,
    }
