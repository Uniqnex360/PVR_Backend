"""add holds and hold_seats tables

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "holds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("showtime_id", sa.Uuid(), nullable=False),
        sa.Column("partner_id", sa.Uuid(), nullable=False),
        sa.Column("end_user_ref", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("quote_total", sa.Integer(), nullable=False),
        sa.Column(
            "currency",
            sa.String(),
            nullable=False,
            server_default=sa.text("'INR'"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["partner_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["showtime_id"], ["showtimes.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "partner_id",
            "end_user_ref",
            "idempotency_key",
            name="uq_hold_partner_enduser_idempotency",
        ),
    )
    op.create_index(
        "ix_holds_showtime_status_expires",
        "holds",
        ["showtime_id", "status", "expires_at"],
    )

    op.create_table(
        "hold_seats",
        sa.Column("hold_id", sa.Uuid(), nullable=False),
        sa.Column("seat_id", sa.Uuid(), nullable=False),
        sa.Column("showtime_id", sa.Uuid(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["hold_id"], ["holds.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"]),
        sa.ForeignKeyConstraint(["showtime_id"], ["showtimes.id"]),
        sa.PrimaryKeyConstraint("hold_id", "seat_id"),
    )
    op.create_index(
        "ux_hold_showtime_seat",
        "hold_seats",
        ["showtime_id", "seat_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_hold_showtime_seat", table_name="hold_seats")
    op.drop_table("hold_seats")
    op.drop_index("ix_holds_showtime_status_expires", table_name="holds")
    op.drop_table("holds")