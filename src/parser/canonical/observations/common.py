"""Shared value objects and constructors for observation adapters."""

from __future__ import annotations

import re
from typing import Any

from src.contracts.patient.v1 import Observation, ObservationComponent
from src.contracts.patient.v1.common import Coding, Quantity, ReferenceRange, SourceReference

from ...normalizers import clean_text, parse_number


def coding(display: str, code: str | None = None, system: str | None = None) -> Coding:
    return Coding(code=code, display=display, system=system)


def quantity(value: Any, unit: Any = None) -> Quantity:
    number = parse_number(value)
    normalized_value: float | str | None = number
    if number is None:
        normalized_value = clean_text(value) or None
    return Quantity(value=normalized_value, unit=clean_text(unit) or None)


def reference_range(value: Any) -> ReferenceRange | None:
    text = clean_text(value)
    if not text:
        return None
    numbers = [
        parse_number(item.replace(",", "."))
        for item in re.findall(r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)", text)
    ]
    parsed = [number for number in numbers if number is not None]
    low = parsed[0] if len(parsed) >= 2 else None
    high = parsed[1] if len(parsed) >= 2 else None
    if len(parsed) == 1:
        if re.search(r"(?:до|<|≤)", text, flags=re.IGNORECASE):
            high = parsed[0]
        elif re.search(r"(?:от|>|≥)", text, flags=re.IGNORECASE):
            low = parsed[0]
    return ReferenceRange(low=low, high=high, text=text)


def blood_pressure_observation(
    *,
    observation_id: str,
    source: SourceReference,
    observed_at: Any,
    category: str,
    systolic: float,
    diastolic: float,
    encounter_id: str | None = None,
    method: str | None = None,
    device: str | None = None,
    context: dict[str, str] | None = None,
) -> Observation:
    return Observation(
        id=observation_id,
        source=source,
        observed_at=observed_at,
        category=category,
        coding=coding("Артериальное давление", "blood-pressure"),
        components=[
            ObservationComponent(
                coding=coding("Систолическое АД", "systolic"),
                value=quantity(systolic, "mmHg"),
            ),
            ObservationComponent(
                coding=coding("Диастолическое АД", "diastolic"),
                value=quantity(diastolic, "mmHg"),
            ),
        ],
        encounter_id=encounter_id,
        method=method,
        device=device,
        context=context or {},
    )


def text_context(**values: Any) -> dict[str, str]:
    return {
        key: normalized
        for key, value in values.items()
        if (normalized := clean_text(value))
    }
