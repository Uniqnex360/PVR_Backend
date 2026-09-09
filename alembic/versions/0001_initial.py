"""0001_initial — every table in one migration.

This is the ONLY migration for Phase 1.  A second migration that adds
booking_seats later means the unique index gets "forgotten in a
follow-up" — the exact class of bug that turns into a double-sell.

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- users --
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.String(),
            nullable=False,
            server_default=sa.text("'customer'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # -- cinemas --
    op.create_table(
        "cinemas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column(
            "timezone",
            sa.String(),
            nullable=False,
            server_default=sa.text("'Asia/Kolkata'"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- screens --
    op.create_table(
        "screens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cinema_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["cinema_id"], ["cinemas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- screen_rows --
    op.create_table(
        "screen_rows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("screen_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("seat_count", sa.Integer(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "seat_count > 0", name="ck_seat_count_positive"
        ),
        sa.CheckConstraint(
            "price_cents >= 0", name="ck_price_cents_non_negative"
        ),
        sa.ForeignKeyConstraint(["screen_id"], ["screens.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "screen_id", "label", name="uq_screen_row_label"
        ),
    )

    # -- seats --
    # NO is_booked / status / occupied column.  Static catalog only.
    op.create_table(
        "seats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("row_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["row_id"], ["screen_rows.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "row_id", "code", name="uq_seat_row_code"
        ),
        sa.UniqueConstraint(
            "row_id", "number", name="uq_seat_row_number"
        ),
    )

    # -- movies --
    op.create_table(
        "movies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("certificate", sa.String(), nullable=False),
        sa.Column("release_year", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- showtimes --
    op.create_table(
        "showtimes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("screen_id", sa.Uuid(), nullable=False),
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column(
            "starts_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("created_by_partner_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"]),
        sa.ForeignKeyConstraint(["screen_id"], ["screens.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # -- bookings --
    op.create_table(
        "bookings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("showtime_id", sa.Uuid(), nullable=False),
        sa.Column("ref_code", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column("idempotency_key", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["showtime_id"], ["showtimes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ref_code"),
        sa.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_booking_user_idempotency",
        ),
    )

    # -- booking_seats --
    # showtime_id is DENORMALIZED ON PURPOSE — see model docstring.
    op.create_table(
        "booking_seats",
        sa.Column("booking_id", sa.Uuid(), nullable=False),
        sa.Column("seat_id", sa.Uuid(), nullable=False),
        sa.Column("showtime_id", sa.Uuid(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["booking_id"], ["bookings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"]),
        sa.ForeignKeyConstraint(["showtime_id"], ["showtimes.id"]),
        sa.PrimaryKeyConstraint("booking_id", "seat_id"),
    )
    op.create_index(
        "ux_showtime_seat",
        "booking_seats",
        ["showtime_id", "seat_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_showtime_seat", table_name="booking_seats")
    op.drop_table("booking_seats")
    op.drop_table("bookings")
    op.drop_table("showtimes")
    op.drop_table("movies")
    op.drop_table("seats")
    op.drop_table("screen_rows")
    op.drop_table("screens")
    op.drop_table("cinemas")
    op.drop_table("users")