"""rbac, security audit, webhook idempotency

Revision ID: 0002_rbac_audit_idempotency
Revises: 0001_initial_schema
Create Date: 2026-04-30 10:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_rbac_audit_idempotency"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    admin_role = sa.Enum("admin", "operator", "viewer", name="admin_role", create_type=False)
    admin_role.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "admins",
        sa.Column("role", admin_role, nullable=False, server_default="admin"),
    )

    op.create_table(
        "security_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("details", sa.String(length=512), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_audits_id"), "security_audits", ["id"], unique=False)
    op.create_index(op.f("ix_security_audits_event_type"), "security_audits", ["event_type"], unique=False)
    op.create_index(op.f("ix_security_audits_actor"), "security_audits", ["actor"], unique=False)
    op.create_index(op.f("ix_security_audits_success"), "security_audits", ["success"], unique=False)
    op.create_index(op.f("ix_security_audits_timestamp"), "security_audits", ["timestamp"], unique=False)

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_key", sa.String(length=128), nullable=False),
        sa.Column("plate_number", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key"),
    )
    op.create_index(op.f("ix_webhook_events_id"), "webhook_events", ["id"], unique=False)
    op.create_index(op.f("ix_webhook_events_event_key"), "webhook_events", ["event_key"], unique=True)
    op.create_index(op.f("ix_webhook_events_plate_number"), "webhook_events", ["plate_number"], unique=False)
    op.create_index(op.f("ix_webhook_events_timestamp"), "webhook_events", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_webhook_events_timestamp"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_plate_number"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_event_key"), table_name="webhook_events")
    op.drop_index(op.f("ix_webhook_events_id"), table_name="webhook_events")
    op.drop_table("webhook_events")

    op.drop_index(op.f("ix_security_audits_timestamp"), table_name="security_audits")
    op.drop_index(op.f("ix_security_audits_success"), table_name="security_audits")
    op.drop_index(op.f("ix_security_audits_actor"), table_name="security_audits")
    op.drop_index(op.f("ix_security_audits_event_type"), table_name="security_audits")
    op.drop_index(op.f("ix_security_audits_id"), table_name="security_audits")
    op.drop_table("security_audits")

    op.drop_column("admins", "role")
    sa.Enum(name="admin_role", create_type=False).drop(op.get_bind(), checkfirst=True)
