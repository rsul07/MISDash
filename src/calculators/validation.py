"""Validation shared by pure clinical formulas."""

from __future__ import annotations

from math import isfinite


def finite_number(value: float, *, name: str) -> float:
    """Return a finite float or reject an unusable calculator input."""

    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def positive_number(value: float, *, name: str) -> float:
    """Return a strictly positive finite float."""

    number = finite_number(value, name=name)
    if number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


def non_negative_number(value: float, *, name: str) -> float:
    """Return a non-negative finite float."""

    number = finite_number(value, name=name)
    if number < 0:
        raise ValueError(f"{name} must not be negative")
    return number
