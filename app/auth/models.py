"""
User model for authentication and customer identity.
"""

from __future__ import annotations

import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String

from app.core.database import Base
from app.shared.timeutil import TZDateTime, utcnow


class User(Base):
    __tablename__ = "users"

    id = Column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, server_default=sa.text("'customer'"))
    created_at = Column(
        TZDateTime,
        nullable=False,
        default=utcnow,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    )