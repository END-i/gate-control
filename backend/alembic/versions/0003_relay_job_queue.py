"""relay job queue for async trigger processing

Revision ID: 0003_relay_job_queue
Revises: 0002_rbac_audit_idempotency
Create Date: 2026-04-30 12:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_relay_job_queue"
down_revision = "0002_rbac_audit_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    relay_job_status = sa.Enum("pending", "processing", "succeeded", "dead_letter", name="relay_job_status")
    relay_job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "relay_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("plate_number", sa.String(length=32), nullable=True),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("status", relay_job_status, nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_relay_jobs_id"), "relay_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_relay_jobs_event_type"), "relay_jobs", ["event_type"], unique=False)
    op.create_index(op.f("ix_relay_jobs_plate_number"), "relay_jobs", ["plate_number"], unique=False)
    op.create_index(op.f("ix_relay_jobs_requested_by"), "relay_jobs", ["requested_by"], unique=False)
    op.create_index(op.f("ix_relay_jobs_status"), "relay_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_relay_jobs_available_at"), "relay_jobs", ["available_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_relay_jobs_available_at"), table_name="relay_jobs")
    op.drop_index(op.f("ix_relay_jobs_status"), table_name="relay_jobs")
    op.drop_index(op.f("ix_relay_jobs_requested_by"), table_name="relay_jobs")
    op.drop_index(op.f("ix_relay_jobs_plate_number"), table_name="relay_jobs")
    op.drop_index(op.f("ix_relay_jobs_event_type"), table_name="relay_jobs")
    op.drop_index(op.f("ix_relay_jobs_id"), table_name="relay_jobs")
    op.drop_table("relay_jobs")

    sa.Enum(name="relay_job_status").drop(op.get_bind(), checkfirst=True)
