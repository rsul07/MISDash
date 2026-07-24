"""Configuration and result models for synthetic MIS exports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


REFERENCE_END = datetime(2026, 5, 20, tzinfo=timezone.utc)
MAX_YEARS = 30


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    """Stable inputs controlling one deterministic synthetic export."""

    seed: int = 42
    years: int = 9
    light: bool = False

    def __post_init__(self) -> None:
        if type(self.seed) is not int:
            raise TypeError("seed must be an integer")
        if type(self.years) is not int:
            raise TypeError("years must be an integer")
        if type(self.light) is not bool:
            raise TypeError("light must be a boolean")
        if not 1 <= self.years <= MAX_YEARS:
            raise ValueError(f"years must be between 1 and {MAX_YEARS}")


@dataclass(frozen=True, slots=True)
class GenerationStats:
    """Compact metadata about a serialized export."""

    line_count: int
    size_bytes: int
    visit_count: int
    laboratory_order_count: int


@dataclass(frozen=True, slots=True)
class GenerationWindow:
    """Internal fixed observation window shared by domain builders."""

    start: datetime
    end: datetime

    @classmethod
    def from_years(cls, years: int) -> GenerationWindow:
        return cls(
            start=REFERENCE_END - timedelta(days=int(years * 365.25)),
            end=REFERENCE_END,
        )

    def fraction(self, value: datetime) -> float:
        return (value - self.start).total_seconds() / (
            self.end - self.start
        ).total_seconds()
