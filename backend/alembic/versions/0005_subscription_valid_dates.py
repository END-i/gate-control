"""Subscription: add valid_from and valid_until to vehicles table

Revision ID: 0005_subscription_valid_dates
Revises: 0004_karsun_access_log_action_type
Create Date: 2026-05-13 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_subscription_valid_dates"
down_revision = "0004_access_log_action_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    with op.batch_alter_table("vehicles", recreate="always" if is_sqlite else "never") as batch_op:
        batch_op.add_column(
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index("ix_vehicles_valid_until", ["valid_until"])


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    with op.batch_alter_table("vehicles", recreate="always" if is_sqlite else "never") as batch_op:
        batch_op.drop_index("ix_vehicles_valid_until")
        batch_op.drop_column("valid_until")
        batch_op.drop_column("valid_from")
