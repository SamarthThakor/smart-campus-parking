"""Record administrator changes without replacing existing parking records."""
from alembic import op
import sqlalchemy as sa
revision = "0002_lot_audit"
down_revision = "0001_initial"
branch_labels = depends_on = None

def upgrade():
    print("Applying 0002_lot_audit: create lot_update audit table", flush=True)
    op.create_table("lot_update",
        sa.Column("update_id", sa.Integer, primary_key=True),
        sa.Column("lot_id", sa.Integer, sa.ForeignKey("parking_lot.lot_id"), nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("changed_at", sa.String(32), nullable=False),
        sa.Column("changes_json", sa.Text, nullable=False))

def downgrade():
    op.drop_table("lot_update")
