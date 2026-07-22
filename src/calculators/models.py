"""Shared value objects for explainable calculated measurements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class CalculatorDefinition:
    """Machine-readable explanation attached to a calculated metric series."""

    code: str
    display: str
    unit: str
    description: str
    inputs: tuple[str, ...]
    purpose: str
    method: str
    standard: str
    limitations: tuple[str, ...]
    references: tuple[str, ...]


@dataclass(frozen=True)
class CalculatedValue:
    """One derived value with the exact canonical records used as inputs."""

    definition: CalculatorDefinition
    observed_at: date | datetime
    value: float
    source_ids: tuple[str, ...]
