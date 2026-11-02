"""Sanitized API errors and durable monthly cost alert delivery."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_errors",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("request_id", sa.String(32), nullable=False),
        sa.Column("route", sa.String(160), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_api_errors_request_id", "api_errors", ["request_id"])
    op.create_index("ix_api_errors_created_at", "api_errors", ["created_at"])
    op.create_table(
        "cost_alerts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("workspace_id", sa.String(32), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("cost_paise", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.BigInteger(), nullable=False),
        sa.Column("lease_until", sa.BigInteger(), nullable=False),
        sa.Column("lease_token", sa.String(32), nullable=True),
        sa.Column("delivered_at", sa.BigInteger(), nullable=True),
        sa.Column("last_error", sa.String(50), nullable=True),
        sa.UniqueConstraint("workspace_id", "period"),
    )
    op.create_index("ix_cost_alerts_workspace_id", "cost_alerts", ["workspace_id"])
    op.create_index("ix_cost_alerts_status", "cost_alerts", ["status"])


def downgrade():
    op.drop_table("cost_alerts")
    op.drop_table("api_errors")
