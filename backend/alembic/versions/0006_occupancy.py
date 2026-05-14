"""Occupancy counter: add occupancy table.

Revision ID: 0006_occupancy
Revises: 0005_subscription_valid_dates
Create Date: 2026-05-13 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_occupancy"
down_revision = "0005_subscription_valid_dates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "occupancy",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("current_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("occupancy")
