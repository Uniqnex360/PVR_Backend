"""Shared Pydantic schemas used across modules."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta