"""Tests for the race-free 2021 CKD-EPI creatinine equation."""

from __future__ import annotations

import pytest

from src.calculators import calculate_egfr_ckd_epi_2021


def test_egfr_accepts_standardized_creatinine_units() -> None:
    from_mg_dl = calculate_egfr_ckd_epi_2021(
        creatinine=1.2,
        creatinine_unit="mg/dL",
        age=50,
        sex="male",
    )
    from_micromoles = calculate_egfr_ckd_epi_2021(
        creatinine=1.2 * 88.4,
        creatinine_unit="мкмоль/л",
        age=50,
        sex="male",
    )

    assert from_mg_dl == pytest.approx(73.73, rel=1e-3)
    assert from_micromoles == pytest.approx(from_mg_dl)


def test_egfr_applies_female_equation_coefficients() -> None:
    result = calculate_egfr_ckd_epi_2021(
        creatinine=0.8,
        creatinine_unit="mg/dL",
        age=60,
        sex="female",
    )

    assert result == pytest.approx(84.30, rel=1e-3)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"age": 17}, "age >= 18"),
        ({"sex": "unknown"}, "sex must be"),
        ({"creatinine": 0}, "must be positive"),
        ({"creatinine_unit": "mmol/L"}, "unsupported creatinine unit"),
    ],
)
def test_egfr_rejects_unsafe_inputs(
    kwargs: dict[str, object],
    message: str,
) -> None:
    inputs: dict[str, object] = {
        "creatinine": 1.0,
        "creatinine_unit": "mg/dL",
        "age": 40,
        "sex": "male",
    }
    inputs.update(kwargs)

    with pytest.raises(ValueError, match=message):
        calculate_egfr_ckd_epi_2021(**inputs)  # type: ignore[arg-type]
