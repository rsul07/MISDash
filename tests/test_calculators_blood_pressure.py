"""Tests for calculations based on a paired BP measurement."""

from __future__ import annotations

import pytest

from src.calculators import calculate_pulse_pressure


def test_pulse_pressure_is_systolic_minus_diastolic() -> None:
    assert calculate_pulse_pressure(systolic=145, diastolic=85) == 60


@pytest.mark.parametrize(
    ("systolic", "diastolic"),
    [(80, 80), (70, 90), (0, 80), (120, float("nan"))],
)
def test_pulse_pressure_rejects_invalid_pairs(
    systolic: float,
    diastolic: float,
) -> None:
    with pytest.raises(ValueError):
        calculate_pulse_pressure(systolic=systolic, diastolic=diastolic)
