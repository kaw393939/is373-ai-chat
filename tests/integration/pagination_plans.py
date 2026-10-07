"""Observe actual page SQL on synthetic, connection-local PostgreSQL tables.

This evidence helper is explicit, not part of the ordinary test suite. It neither
migrates nor clears the supplied database. Temporary copies shadow the public
tables for this connection and disappear on close. See book/03-data.md.
"""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import asyncpg
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import make_url

from app.models import Conversation, Generation, Message, User
from app.pagination import encode_cursor, page_rows
from tests.targets import disposable_database

TABLES = ("users", "conversations", "messages", "generations")
COUNTS = {"users": 5000, "conversations": 10000, "messages": 20000, "generations": 5000}
OWNER = f"{1:032x}"
CONVERSATION = f"{1:032x}"
SECRET = "synthetic-plan-cursor-only"


class Capture:
    """Capture the statement built by the production pagination helper."""

    async def scalars(self, statement):
        self.statement = statement
        return SimpleNamespace(all=lambda: [])


async def query(model, statement, position=None):
    capture = Capture()
    cursor = (
        encode_cursor(
            SimpleNamespace(created_at=position // 4, id=f"{position:032x}"), "plan", SECRET
        )
        if position is not None
        else None
    )
    await page_rows(capture, model, statement, 50, cursor, "plan", SECRET)
    return str(
        capture.statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


async def statements():
    conversations = select(Conversation).where(Conversation.user_id == OWNER)
    messages = select(Message).where(Message.conversation_id == CONVERSATION)
    runs = select(Generation).where(Generation.conversation_id == CONVERSATION)
    cases = [
        ("conversation_owner_first", Conversation, conversations, None),
        ("conversation_owner_deep", Conversation, conversations, 500),
        (
            "conversation_regular_first",
            Conversation,
            select(Conversation).where(Conversation.user_id == f"{2:032x}"),
            None,
        ),
        ("message_owned_first", Message, messages, None),
        ("message_owned_deep", Message, messages, 1000),
        ("run_owned_first", Generation, runs, None),
        ("run_owned_deep", Generation, runs, 500),
        ("admin_first", User, select(User), None),
        ("admin_deep", User, select(User), 1000),
    ]
    for name, value in (("common", "lesson"), ("rare", "needle"), ("absent", "unmatched")):
        cases.append(
            (
                f"conversation_search_{name}",
                Conversation,
                conversations.where(Conversation.title.icontains(value, autoescape=True)),
                None,
            )
        )
    for name, value in (
        ("common", "example.invalid"),
        ("rare", "learner-1@"),
        ("absent", "unmatched"),
    ):
        cases.append(
            (
                f"admin_search_{name}",
                User,
                select(User).where(User.email.icontains(value, autoescape=True)),
                None,
            )
        )
    return {
        name: await query(model, statement, position) for name, model, statement, position in cases
    }


async def populate(connection):
    for table in TABLES:
        await connection.execute(
            f'CREATE TEMP TABLE "{table}" (LIKE public."{table}" INCLUDING ALL)'
        )
    # All writes explicitly use pg_temp; an absent temporary table cannot send a
    # fixture write to the public schema. Generated identifiers are synthetic.
    await connection.execute("""
        INSERT INTO pg_temp.users
            (id,email,password_hash,role,active,approved,email_verified,mfa_last_counter,created_at)
        SELECT lpad(to_hex(i),32,'0'),'learner-'||i||'@example.invalid','not-an-authenticator',
               'user',true,true,true,-1,floor(i/4.0)
        FROM generate_series(1,5000) i
    """)
    await connection.execute("""
        INSERT INTO pg_temp.conversations (id,user_id,title,created_at)
        SELECT lpad(to_hex(i),32,'0'),
               lpad(to_hex(CASE WHEN i<=2000 THEN 1 ELSE 2+(i%99) END),32,'0'),
               CASE WHEN i=1 THEN 'old needle lesson' ELSE 'lesson '||i END,floor(i/4.0)
        FROM generate_series(1,10000) i
    """)
    await connection.execute("""
        INSERT INTO pg_temp.messages (id,conversation_id,role,content,created_at)
        SELECT lpad(to_hex(i),32,'0'),
               lpad(to_hex(CASE WHEN i<=5000 THEN 1 ELSE 2+(i%9999) END),32,'0'),
               'assistant','synthetic message '||i,floor(i/4.0)
        FROM generate_series(1,20000) i
    """)
    await connection.execute("""
        INSERT INTO pg_temp.generations
            (id,user_id,conversation_id,request_key,message_id,status,reserved_units,
             actual_tokens,created_at,expires_at,cancel_requested)
        SELECT lpad(to_hex(i),32,'0'),c.user_id,c.id,'synthetic-'||i,m.id,
               'complete',8,4,floor(i/4.0),floor(i/4.0)+150,false
        FROM generate_series(1,5000) i
        JOIN pg_temp.messages m
          ON m.id=lpad(to_hex(CASE WHEN i<=2000 THEN i ELSE i+3000 END),32,'0')
        JOIN pg_temp.conversations c ON c.id=m.conversation_id
    """)
    for table in TABLES:
        await connection.execute(f'ANALYZE pg_temp."{table}"')
        count = await connection.fetchval(f'SELECT count(*) FROM pg_temp."{table}"')
        assert count == COUNTS[table], (table, count)


async def observe(value, acknowledgement, destination):
    disposable_database(value, acknowledgement=acknowledgement)  # Before any connection.
    url = make_url(value)
    if url.drivername != "postgresql+asyncpg":
        raise ValueError("This evidence helper requires guarded loopback PostgreSQL")
    connection = await asyncpg.connect(
        url.set(drivername="postgresql").render_as_string(hide_password=False)
    )
    try:
        await connection.execute("SET statement_timeout='30s'")
        # This helper shares the small rehearsal server's resource ceiling.
        # The successful plan evidence records these per-session settings.
        await connection.execute("SET work_mem='512kB'")
        await connection.execute("SET temp_buffers='1MB'")
        public_counts = {
            table: await connection.fetchval(f'SELECT count(*) FROM public."{table}"')
            for table in TABLES
        }
        revision = await connection.fetchval("SELECT version_num FROM public.alembic_version")
        await populate(connection)
        await connection.execute("SET search_path=pg_temp,public")
        plans = {}
        for name, sql in (await statements()).items():
            # Verify all unqualified ORM table names resolve to this connection's
            # temporary namespace before executing the captured read-only SQL.
            for table in TABLES:
                namespace = await connection.fetchval(
                    """
                    SELECT n.nspname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                    WHERE c.oid=to_regclass($1)
                """,
                    table,
                )
                assert namespace.startswith("pg_temp_"), (table, namespace)
            raw = await connection.fetchval(
                "EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) " + sql
            )
            plan = json.loads(raw)[0]
            assert plan["Plan"]["Actual Rows"] <= 51
            plans[name] = {"sql": sql, "explain": plan}
        after_counts = {
            table: await connection.fetchval(f'SELECT count(*) FROM public."{table}"')
            for table in TABLES
        }
        assert after_counts == public_counts, "Public row counts changed during isolated review"
        indexes = await connection.fetch(
            """
            SELECT tablename,indexname,indexdef FROM pg_indexes
            WHERE schemaname='public' AND tablename=ANY($1::text[])
            ORDER BY tablename,indexname
        """,
            list(TABLES),
        )
        root = Path(__file__).resolve().parents[2]
        document = {
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "source-query-plan-review",
            "target": "guarded-loopback-disposable-postgresql/connection-local-temporary-tables",
            "postgresql_version": await connection.fetchval("SHOW server_version"),
            "schema_revision": revision,
            "source": "app.pagination.page_rows captured with PostgreSQL SQLAlchemy compilation",
            "source_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip(),
            "source_sha256": {
                str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (
                    root / "app/main.py",
                    root / "app/models.py",
                    root / "app/pagination.py",
                )
            },
            "page_limit": 50,
            "probe_limit": 51,
            "fixture_rows": COUNTS,
            "fixture_distribution": {
                "hot_owner_conversations": 2000,
                "regular_owner_conversations": 81,
                "hot_conversation_messages": 5000,
                "hot_conversation_runs": 2000,
                "timestamp_ties": "four generated rows per timestamp",
                "content": "synthetic identifiers and example.invalid addresses only",
            },
            "settings": {
                name: await connection.fetchval(f"SHOW {name}")
                for name in (
                    "work_mem",
                    "temp_buffers",
                    "shared_buffers",
                    "max_parallel_workers_per_gather",
                    "enable_seqscan",
                    "enable_indexscan",
                )
            },
            "public_indexes_copied": [dict(row) for row in indexes],
            "public_row_counts_unchanged": after_counts == public_counts,
            "plans": plans,
            "limitations": [
                "No public application tables were populated, reset or indexed.",
                "Temporary-table local-buffer timings are observations, not production latency or load capacity.",
                "LIKE INCLUDING ALL copies column/index definitions but not foreign keys; synthetic relationships are populated consistently and HTTP ownership has separate regression tests.",
                "The LIMIT bounds returned rows; sorting, cursor filtering and substring search can examine more rows.",
                "Ownership authorization occurs before message/run selection; this plan review is not an HTTP authorization test.",
                "No index or production schema change was made by this helper.",
            ],
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(document, indent=2) + "\n")
        print(
            f"Observed {len(plans)} bounded plans on synthetic temporary tables; saved {destination}"
        )
        for name, observed in plans.items():
            result = observed["explain"]
            print(
                f"{name}: returned={result['Plan']['Actual Rows']} execution_ms={result['Execution Time']:.3f}"
            )
    finally:
        await connection.close()  # PostgreSQL removes every temporary fixture and index.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".state/pagination-plans.json"))
    args = parser.parse_args()
    asyncio.run(
        observe(
            os.environ.get("TEST_DATABASE_URL", ""), os.environ.get("TEST_ALLOW_RESET"), args.output
        )
    )


if __name__ == "__main__":
    main()
