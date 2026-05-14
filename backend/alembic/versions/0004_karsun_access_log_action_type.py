"""Karsun: action_type + admin_id in access_logs; extend vehicle_status enum

Revision ID: 0004_karsun_access_log_action_type
Revises: 0003_relay_job_queue
Create Date: 2026-05-13 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_karsun_access_log_action_type"
down_revision = "0003_relay_job_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Extend vehicle_status enum with 'denied' and 'blacklist'.
    # PostgreSQL requires explicit ALTER TYPE; SQLite stores enums as VARCHAR
    # so no type alteration is needed.
    if dialect == "postgresql":
        bind.execute(sa.text("ALTER TYPE vehicle_status ADD VALUE IF NOT EXISTS 'denied'"))
        bind.execute(sa.text("ALTER TYPE vehicle_status ADD VALUE IF NOT EXISTS 'blacklist'"))

    # Add action_type column: records whether the entry was camera-autonomous
    # (auto_entry) or an operator-initiated manual open (manual_entry).
    op.add_column(
        "access_logs",
        sa.Column("action_type", sa.String(32), nullable=True, server_default="auto_entry"),
    )

    # Add admin_id nullable column: set for manual_entry records to identify
    # the operator who triggered the open.
    op.add_column(
        "access_logs",
        sa.Column("admin_id", sa.Integer(), nullable=True),
    )

    # On PostgreSQL add a proper FK constraint; SQLite doesn't enforce FK
    # constraints by default so we skip the constraint creation there.
    if dialect == "postgresql":
        op.create_foreign_key(
            "fk_access_logs_admin_id",
            "access_logs", "admins",
            ["admin_id"], ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.drop_constraint("fk_access_logs_admin_id", "access_logs", type_="foreignkey")

    op.drop_column("access_logs", "admin_id")
    op.drop_column("access_logs", "action_type")

    # Note: PostgreSQL ENUM values cannot be removed without recreating the type.
    # The 'denied' and 'blacklist' values remain in vehicle_status after downgrade.
