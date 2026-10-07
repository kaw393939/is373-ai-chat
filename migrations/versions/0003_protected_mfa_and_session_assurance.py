"""Additive MFA state; old sessions remain unassured until policy enforcement."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("mfa_secret", sa.Text()))
    op.add_column(
        "users", sa.Column("mfa_last_counter", sa.Integer(), nullable=False, server_default="-1")
    )
    op.add_column("users", sa.Column("mfa_pending_secret", sa.Text()))
    op.add_column("users", sa.Column("mfa_pending_expires_at", sa.Float()))
    op.add_column(
        "sessions",
        sa.Column("mfa_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "mfa_challenges",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("expires_at", sa.Float(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("enrollment_secret", sa.Text()),
    )
    op.create_index("ix_mfa_challenges_user_id", "mfa_challenges", ["user_id"])
    op.create_table(
        "mfa_recovery_codes",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("used", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_mfa_recovery_codes_user_id", "mfa_recovery_codes", ["user_id"])


def downgrade():
    op.drop_table("mfa_recovery_codes")
    op.drop_table("mfa_challenges")
    op.drop_column("sessions", "mfa_verified")
    op.drop_column("users", "mfa_pending_expires_at")
    op.drop_column("users", "mfa_pending_secret")
    op.drop_column("users", "mfa_last_counter")
    op.drop_column("users", "mfa_secret")
