"""Normalization helpers for dirty MIS scalar values."""

from __future__ import annotations

import math
import re
from datetime import date, datetime, timezone
from typing import Any

from .constants import MISSING_STRINGS


def normalize_date(value: Any) -> str | None:
    """Convert a supported dirty date value to ``YYYY-MM-DD``."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        if float(value).is_integer() and 1000 <= int(value) <= 9999:
            return None
        if float(value).is_integer() and re.fullmatch(r"\d{8}", str(int(value))):
            try:
                return datetime.strptime(str(int(value)), "%Y%m%d").date().isoformat()
            except ValueError:
                pass
        return _date_from_timestamp(value)
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if raw.casefold() in MISSING_STRINGS:
        return None

    if re.fullmatch(r"\d{8}", raw):
        try:
            return datetime.strptime(raw, "%Y%m%d").date().isoformat()
        except ValueError:
            pass

    if re.fullmatch(r"\d{4}", raw) and 1000 <= int(raw) <= 9999:
        return None
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        try:
            return _date_from_timestamp(float(raw))
        except ValueError:
            return None

    iso_candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        return datetime.fromisoformat(iso_candidate).date().isoformat()
    except ValueError:
        pass

    formats = (
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d.%m.%y",
        "%d/%m/%y",
        "%d.%m.%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%d.%m.%y %H:%M",
        "%d/%m/%y %H:%M",
    )
    for date_format in formats:
        try:
            return datetime.strptime(raw, date_format).date().isoformat()
        except ValueError:
            continue
    return None


def _date_from_timestamp(value: int | float) -> str | None:
    if not math.isfinite(float(value)):
        return None
    timestamp = float(value)
    while abs(timestamp) > 10_000_000_000:
        timestamp /= 1000
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def parse_number(value: Any) -> float | None:
    """Convert a number or a decimal string (including comma decimals)."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if not isinstance(value, str):
        return None

    raw = value.strip().replace("\u00a0", "")
    if raw.casefold() in MISSING_STRINGS:
        return None
    raw = raw.replace(" ", "").replace(",", ".")
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", raw):
        return None
    try:
        number = float(raw)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


parse_date = normalize_date
normalize_number = parse_number


def clean_text(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        cleaned = " ".join(value.replace("\u00a0", " ").split())
        return "" if cleaned.casefold() in MISSING_STRINGS else cleaned
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return "; ".join(filter(None, (clean_text(item) for item in value)))
    return ""


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().casefold() not in MISSING_STRINGS
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def clean_name(value: Any) -> str:
    text = clean_text(value)
    return text.title() if text and text == text.upper() else text


def normalize_gender(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, (int, float)):
        if value == 1:
            return "Мужской"
        if value == 2:
            return "Женский"
    text = clean_text(value)
    normalized = text.casefold()
    if normalized in {"м", "муж", "мужской", "male", "m", "1"}:
        return "Мужской"
    if normalized in {"ж", "жен", "женский", "female", "f", "2"}:
        return "Женский"
    return text


def age_from_values(raw_age: Any, birth_date: str | None) -> int | None:
    age = parse_number(raw_age)
    if age is not None and age >= 0:
        return int(age)
    if birth_date is None:
        return None
    try:
        born = date.fromisoformat(birth_date)
    except ValueError:
        return None
    today = date.today()
    calculated = today.year - born.year - (
        (today.month, today.day) < (born.month, born.day)
    )
    return calculated if calculated >= 0 else None


def valid_number(
    value: Any,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    number = parse_number(value)
    if number is None:
        return None
    if minimum is not None and number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    return number


def valid_bp_pair(systolic: Any, diastolic: Any) -> tuple[float, float] | None:
    normalized_systolic = valid_number(systolic, 60, 300)
    normalized_diastolic = valid_number(diastolic, 30, 200)
    if (
        normalized_systolic is None
        or normalized_diastolic is None
        or normalized_systolic <= normalized_diastolic
    ):
        return None
    return normalized_systolic, normalized_diastolic
