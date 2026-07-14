"""Date and datetime normalization for canonical clinical events."""

from __future__ import annotations

import math
import re
from datetime import date, datetime, timezone
from typing import Any

from ..constants import MISSING_STRINGS


def parse_clinical_date(value: Any) -> date | datetime | None:
    """Parse a supported date while preserving time when it is present."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return _numeric_date(value)
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if raw.casefold() in MISSING_STRINGS or re.fullmatch(r"\d{4}", raw):
        return None
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        try:
            return _numeric_date(float(raw))
        except ValueError:
            return None

    iso_candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        return parsed if _contains_time(raw) else parsed.date()
    except ValueError:
        pass

    formats = (
        ("%Y%m%d", False),
        ("%d.%m.%Y", False),
        ("%d/%m/%Y", False),
        ("%d.%m.%y", False),
        ("%d/%m/%y", False),
        ("%d.%m.%Y %H:%M", True),
        ("%d/%m/%Y %H:%M", True),
        ("%d.%m.%y %H:%M", True),
        ("%d/%m/%y %H:%M", True),
    )
    for date_format, has_time in formats:
        try:
            parsed = datetime.strptime(raw, date_format)
            return parsed if has_time else parsed.date()
        except ValueError:
            continue
    return None


def _numeric_date(value: int | float) -> date | datetime | None:
    number = float(value)
    if not math.isfinite(number):
        return None
    integer = int(number)
    if number.is_integer() and 1000 <= integer <= 9999:
        return None
    if number.is_integer() and re.fullmatch(r"\d{8}", str(integer)):
        try:
            return datetime.strptime(str(integer), "%Y%m%d").date()
        except ValueError:
            pass
    while abs(number) > 10_000_000_000:
        number /= 1000
    try:
        return datetime.fromtimestamp(number, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _contains_time(value: str) -> bool:
    return "T" in value or bool(re.search(r"\s\d{1,2}:\d{2}", value))
