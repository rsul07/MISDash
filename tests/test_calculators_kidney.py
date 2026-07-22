"""Tests for KDIGO measurement categories."""

from __future__ import annotations

import pytest

from src.calculators import (
    classify_albuminuria_category,
    classify_egfr_category,
)


@pytest.mark.parametrize(
    ("value", "category"),
    [
        (90, "G1"),
        (89.99, "G2"),
        (60, "G2"),
        (59.99, "G3a"),
        (45, "G3a"),
        (44.99, "G3b"),
        (30, "G3b"),
        (29.99, "G4"),
        (15, "G4"),
        (14.99, "G5"),
    ],
)
def test_egfr_categories_use_unrounded_thresholds(
    value: float,
    category: str,
) -> None:
    assert classify_egfr_category(value) == category


@pytest.mark.parametrize(
    ("value", "category"),
    [(0, "A1"), (2.99, "A1"), (3, "A2"), (30, "A2"), (30.01, "A3")],
)
def test_albuminuria_categories_use_mg_per_mmol(
    value: float,
    category: str,
) -> None:
    assert classify_albuminuria_category(value) == category


@pytest.mark.parametrize(
    "calculator",
    [classify_egfr_category, classify_albuminuria_category],
)
def test_kidney_categories_reject_negative_values(calculator: object) -> None:
    with pytest.raises(ValueError):
        calculator(-1)  # type: ignore[operator]
