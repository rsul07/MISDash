"""Helpers that intentionally introduce realistic dirty scalar formats."""

from __future__ import annotations

import random
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any


DATE_STYLES = [
    "dd.mm.yyyy",
    "iso",
    "isoT",
    "yyyymmdd",
    "unix_str",
    "dd/mm/yy",
]


def messy_date(
    value: datetime,
    rnd: random.Random,
    styles: Sequence[str] = DATE_STYLES,
) -> str:
    style = rnd.choice(styles)
    if style == "dd.mm.yyyy":
        return value.strftime("%d.%m.%Y")
    if style == "iso":
        return value.strftime("%Y-%m-%d")
    if style == "isoT":
        return value.strftime("%Y-%m-%dT%H:%M:%S")
    if style == "yyyymmdd":
        return value.strftime("%Y%m%d")
    if style == "unix_str":
        aware = (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )
        return str(int(aware.timestamp()))
    if style == "dd/mm/yy":
        return value.strftime("%d/%m/%y")
    return value.isoformat()


def messy_num(value: Any, rnd: random.Random) -> Any:
    """Return a number directly or in one of several string forms."""

    choice = rnd.random()
    if isinstance(value, float):
        value = round(value, 2)
    if choice < 0.35:
        return value
    if choice < 0.7:
        return str(value).replace(".", ",")
    if choice < 0.85:
        return str(value)
    return f" {value} ".replace(".", ",")


def maybe_missing(
    value: Any,
    rnd: random.Random,
    probability: float = 0.06,
) -> Any:
    if rnd.random() < probability:
        return rnd.choice([None, "", "-", "нет данных", "н/д"])
    return value
