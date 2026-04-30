"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-29 19:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # create_type=False: we manage CREATE TYPE ourselves via .create() below;
    # prevents op.create_table from issuing a second CREATE TYPE and raising
    # DuplicateObjectError on asyncpg when the type already exists.
    vehicle_status = sa.Enum("allowed", "blocked", name="vehicle_status", create_type=False)
    vehicle_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admins_id"), "admins", ["id"], unique=False)
    op.create_index(op.f("ix_admins_username"), "admins", ["username"], unique=True)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("license_plate", sa.String(length=32), nullable=False),
        sa.Column("status", vehicle_status, nullable=False),
        sa.Column("owner_info", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicles_id"), "vehicles", ["id"], unique=False)
    op.create_index(op.f("ix_vehicles_license_plate"), "vehicles", ["license_plate"], unique=True)

    op.create_table(
        "access_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("license_plate", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("access_granted", sa.Boolean(), nullable=False),
        sa.Column("image_path", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_logs_id"), "access_logs", ["id"], unique=False)
    op.create_index(op.f("ix_access_logs_license_plate"), "access_logs", ["license_plate"], unique=False)
    op.create_index(op.f("ix_access_logs_timestamp"), "access_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_access_logs_timestamp"), table_name="access_logs")
    op.drop_index(op.f("ix_access_logs_license_plate"), table_name="access_logs")
    op.drop_index(op.f("ix_access_logs_id"), table_name="access_logs")
    op.drop_table("access_logs")

    op.drop_index(op.f("ix_vehicles_license_plate"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_id"), table_name="vehicles")
    op.drop_table("vehicles")

    op.drop_index(op.f("ix_admins_username"), table_name="admins")
    op.drop_index(op.f("ix_admins_id"), table_name="admins")
    op.drop_table("admins")

    sa.Enum(name="vehicle_status", create_type=False).drop(op.get_bind(), checkfirst=True)
