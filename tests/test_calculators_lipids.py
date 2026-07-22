"""Tests for deterministic lipid calculations."""

from __future__ import annotations

import pytest

from src.calculators import (
    calculate_non_hdl_cholesterol,
    calculate_sampson_ldl_cholesterol,
)


def test_non_hdl_uses_total_and_hdl_from_same_unit() -> None:
    result = calculate_non_hdl_cholesterol(
        total_cholesterol=5.2,
        hdl_cholesterol=1.3,
    )

    assert result == pytest.approx(3.9)


def test_non_hdl_rejects_inconsistent_components() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        calculate_non_hdl_cholesterol(
            total_cholesterol=1.0,
            hdl_cholesterol=1.2,
        )


def test_sampson_ldl_matches_published_equation() -> None:
    result = calculate_sampson_ldl_cholesterol(
        total_cholesterol_mg_dl=200,
        hdl_cholesterol_mg_dl=50,
        triglycerides_mg_dl=150,
    )

    assert result == pytest.approx(123.3973, rel=1e-4)


def test_sampson_ldl_rejects_unvalidated_triglycerides() -> None:
    with pytest.raises(ValueError, match="above 800"):
        calculate_sampson_ldl_cholesterol(
            total_cholesterol_mg_dl=250,
            hdl_cholesterol_mg_dl=40,
            triglycerides_mg_dl=801,
        )


def test_sampson_ldl_rejects_negative_result() -> None:
    with pytest.raises(ValueError, match="negative LDL"):
        calculate_sampson_ldl_cholesterol(
            total_cholesterol_mg_dl=40,
            hdl_cholesterol_mg_dl=39,
            triglycerides_mg_dl=200,
        )
