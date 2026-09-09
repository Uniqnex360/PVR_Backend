"""
Base domain exceptions.  Plain Exception subclasses — never HTTPException.

Every module's interfaces.py derives its specific errors from these.
"""


class DomainError(Exception):
    """Root for all domain-level errors."""


class NotFoundError(DomainError):
    """Requested entity does not exist."""


class DuplicateError(DomainError):
    """Entity with the same natural key already exists."""


class ConflictError(DomainError):
    """State conflict — e.g. seat already booked for this showtime."""