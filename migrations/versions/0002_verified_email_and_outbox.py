"""Verified addresses, purpose-bound links and encrypted mail outbox."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # Existing administrator-approved users retain access; new enrollment verifies mail.
    op.add_column(
        "users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.add_column(
        "recovery_tokens",
        sa.Column("purpose", sa.String(16), nullable=False, server_default="reset"),
    )
    op.create_table(
        "email_outbox",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.Float(), nullable=False),
        sa.Column("next_attempt", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.Column("provider_id", sa.String(128)),
    )
    op.create_index("ix_email_outbox_status", "email_outbox", ["status"])


def downgrade():
    op.drop_table("email_outbox")
    op.drop_column("recovery_tokens", "purpose")
    op.drop_column("users", "email_verified")
