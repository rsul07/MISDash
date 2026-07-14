"""Regular-expression extraction from free-form clinical text."""

from __future__ import annotations

import re
from typing import Any

from .normalizers import clean_text, valid_bp_pair


_BP_RE = re.compile(
    r"(?:\b[АA]Д\b|\bА\s*/\s*Д\b|\bAD\b|"
    r"артериальн\w*\s+давлен\w*|\bдавлен\w*)"
    r"[^0-9]{0,50}"
    r"(?P<sys>\d{2,3})\s*(?:[/\\-]|\bна\b)\s*(?P<dia>\d{2,3})\b",
    flags=re.IGNORECASE,
)
_HEART_RATE_RE = re.compile(
    r"\b(?:ЧСС|пульс(?:а)?|HR)\b[^0-9]{0,20}(?P<heart_rate>\d{2,3})\b",
    flags=re.IGNORECASE,
)


def extract_vitals_from_text(value: Any) -> dict[str, int | None]:
    """Extract a valid blood-pressure pair and heart rate from text."""

    text = clean_text(value)
    result: dict[str, int | None] = {
        "sys_bp": None,
        "dia_bp": None,
        "heart_rate": None,
    }
    if not text:
        return result

    for bp_match in _BP_RE.finditer(text):
        systolic = int(bp_match.group("sys"))
        diastolic = int(bp_match.group("dia"))
        if valid_bp_pair(systolic, diastolic) is not None:
            result["sys_bp"] = systolic
            result["dia_bp"] = diastolic
            break

    for heart_rate_match in _HEART_RATE_RE.finditer(text):
        heart_rate = int(heart_rate_match.group("heart_rate"))
        if 20 <= heart_rate <= 250:
            result["heart_rate"] = heart_rate
            break
    return result
