"""Shared deterministic helpers for backend projections."""

from __future__ import annotations

from datetime import date, datetime


def chronological_key(value: date | datetime | None) -> tuple[bool, str]:
    """Build a comparable key for mixed date and datetime values."""

    return value is not None, value.isoformat() if value is not None else ""
