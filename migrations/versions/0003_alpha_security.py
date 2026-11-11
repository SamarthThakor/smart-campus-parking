"""Persistent revocable sessions and bounded authentication counters."""

from alembic import op
import sqlalchemy as sa

revision = "0003_alpha_security"
down_revision = "0002_lot_audit"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "auth_session",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("user.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.Integer, nullable=False),
    )
    op.create_index("ix_auth_session_expiry", "auth_session", ["expires_at"])
    op.create_table(
        "auth_limit",
        sa.Column("key_hash", sa.String(64), primary_key=True),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("expires_at", sa.Integer, nullable=False),
    )
    op.create_index("ix_auth_limit_expiry", "auth_limit", ["expires_at"])


def downgrade():
    op.drop_table("auth_limit")
    op.drop_table("auth_session")
