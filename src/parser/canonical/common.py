"""Shared helpers for canonical MIS adapters."""

from __future__ import annotations

from typing import Any

from src.contracts.patient.v1.common import SourceReference

from ..normalizers import clean_text


def event_id(prefix: str, index: int, source_id: Any = None) -> str:
    """Return a deterministic event ID, preferring the MIS identifier."""

    normalized_id = clean_text(source_id)
    return normalized_id or f"{prefix}-{index + 1}"


def source_reference(
    block: str,
    index: int | None = None,
    source_id: Any = None,
) -> SourceReference:
    normalized_id = clean_text(source_id) or None
    path = block if index is None else f"{block}[{index}]"
    return SourceReference(block=block, source_id=normalized_id, path=path)


def original_date_text(value: Any, parsed: object | None) -> str | None:
    """Keep an imprecise or invalid source date without inventing precision."""

    text = clean_text(value)
    return text or None if parsed is None else None
