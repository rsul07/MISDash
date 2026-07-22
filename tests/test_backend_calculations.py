"""Tests for binding canonical records to pure clinical calculators."""

from __future__ import annotations

from datetime import date

import pytest

from src.backend.calculations import calculate_record_metrics
from src.backend.metrics import build_metric_series
from src.contracts.patient.v1 import (
    Observation,
    ObservationComponent,
    Patient,
    PatientRecord,
)
from src.contracts.patient.v1.common import Coding, Quantity, SourceReference


SOURCE = SourceReference(block="test")


def test_record_calculates_egfr_with_age_on_analysis_date() -> None:
    record = _record(
        _laboratory(
            "creatinine-1",
            "report-1",
            date(2025, 3, 13),
            "Креатинин",
            88.4,
            "мкмоль/л",
        ),
        birth_date=date(1980, 3, 14),
        gender="male",
    )

    values = calculate_record_metrics(record)

    assert len(values) == 1
    assert values[0].definition.code == "egfr-ckd-epi-2021"
    assert values[0].value == pytest.approx(95.18, rel=1e-3)
    assert values[0].source_ids == ("creatinine-1",)
    assert values[0].interpretation == "G1"


def test_record_skips_egfr_without_explicit_unit_or_demographics() -> None:
    no_unit = _record(
        _laboratory(
            "creatinine-1",
            "report-1",
            date(2025, 1, 1),
            "Креатинин",
            90,
            None,
        ),
        birth_date=date(1980, 1, 1),
        gender="male",
    )
    no_birth_date = _record(
        _laboratory(
            "creatinine-2",
            "report-2",
            date(2025, 1, 1),
            "Креатинин",
            90,
            "мкмоль/л",
        ),
        gender="male",
    )

    assert calculate_record_metrics(no_unit) == []
    assert calculate_record_metrics(no_birth_date) == []


def test_record_calculates_lipids_only_inside_one_report() -> None:
    record = _record(
        _laboratory("tc", "lipid-1", date(2025, 1, 1), "Холестерин общий", 5.2),
        _laboratory("hdl", "lipid-1", date(2025, 1, 1), "ЛПВП", 1.3),
        _laboratory("tg", "lipid-1", date(2025, 1, 1), "Триглицериды", 1.5),
        _laboratory("other-hdl", "lipid-2", date(2025, 1, 1), "ЛПВП", 2.0),
    )

    values = {item.definition.code: item for item in calculate_record_metrics(record)}

    assert values["non-hdl-cholesterol"].value == pytest.approx(3.9)
    assert values["non-hdl-cholesterol"].source_ids == ("tc", "hdl")
    assert values["calculated-ldl-cholesterol"].value == pytest.approx(
        3.287,
        rel=1e-3,
    )
    assert values["calculated-ldl-cholesterol"].source_ids == (
        "tc",
        "hdl",
        "tg",
    )


def test_direct_ldl_prevents_restorative_estimate() -> None:
    record = _record(
        _laboratory("tc", "lipid-1", date(2025, 1, 1), "Холестерин общий", 5.2),
        _laboratory("hdl", "lipid-1", date(2025, 1, 1), "ЛПВП", 1.3),
        _laboratory("tg", "lipid-1", date(2025, 1, 1), "Триглицериды", 1.5),
        _laboratory("ldl", "lipid-1", date(2025, 1, 1), "ЛПНП", 3.1),
    )

    codes = [item.definition.code for item in calculate_record_metrics(record)]

    assert codes == ["non-hdl-cholesterol"]


def test_unitless_direct_ldl_does_not_block_safe_estimate() -> None:
    record = _record(
        _laboratory("tc", "lipid-1", date(2025, 1, 1), "Холестерин общий", 5.2),
        _laboratory("hdl", "lipid-1", date(2025, 1, 1), "ЛПВП", 1.3),
        _laboratory("tg", "lipid-1", date(2025, 1, 1), "Триглицериды", 1.5),
        _laboratory(
            "ldl-without-unit",
            "lipid-1",
            date(2025, 1, 1),
            "ЛПНП",
            3.1,
            None,
        ),
    )

    codes = [item.definition.code for item in calculate_record_metrics(record)]

    assert codes == ["non-hdl-cholesterol", "calculated-ldl-cholesterol"]


def test_record_calculates_pulse_pressure_only_from_one_bp_observation() -> None:
    paired = Observation(
        id="bp-1",
        source=SOURCE,
        observed_at=date(2025, 1, 1),
        category="self-monitoring",
        coding=Coding(code="blood-pressure", display="АД"),
        components=[
            _component("systolic", 145),
            _component("diastolic", 85),
        ],
    )
    unpaired = Observation(
        id="bp-2",
        source=SOURCE,
        observed_at=date(2025, 1, 2),
        category="self-monitoring",
        coding=Coding(code="blood-pressure", display="АД"),
        components=[_component("systolic", 150)],
    )

    values = calculate_record_metrics(_record(paired, unpaired))

    assert len(values) == 1
    assert values[0].definition.code == "pulse-pressure"
    assert values[0].value == 60
    assert values[0].source_ids == ("bp-1",)


def test_metric_projection_exposes_calculation_and_acr() -> None:
    record = _record(
        Observation(
            id="bp-1",
            source=SOURCE,
            observed_at=date(2025, 1, 1),
            category="vital-signs",
            coding=Coding(code="blood-pressure", display="АД"),
            components=[
                _component("systolic", 140),
                _component("diastolic", 80),
            ],
        ),
        _laboratory(
            "acr-1",
            "acr-report",
            date(2025, 1, 2),
            "Альбумин/креатинин (моча)",
            8.5,
            "мг/ммоль",
        ),
    )

    metrics = {item.code: item for item in build_metric_series(record)}

    pulse_pressure = metrics["pulse-pressure"]
    assert pulse_pressure.calculation is not None
    assert pulse_pressure.calculation.method == (
        "Pulse pressure = systolic BP - diastolic BP"
    )
    assert pulse_pressure.points[0].source_category == "calculated"
    assert pulse_pressure.points[0].source_ids == ["bp-1"]
    assert metrics["urine-albumin-creatinine-ratio"].points[0].value == 8.5
    assert metrics["urine-albumin-creatinine-ratio"].points[0].interpretation == "A2"


def _record(
    *observations: Observation,
    birth_date: date | None = None,
    gender: str | None = None,
) -> PatientRecord:
    return PatientRecord(
        patient=Patient(
            id="patient-1",
            full_name="Пациент",
            birth_date=birth_date,
            gender=gender,
            source=SOURCE,
        ),
        observations=list(observations),
    )


def _laboratory(
    observation_id: str,
    report_id: str,
    observed_at: date,
    display: str,
    value: float,
    unit: str | None = "ммоль/л",
) -> Observation:
    return Observation(
        id=observation_id,
        source=SOURCE,
        observed_at=observed_at,
        category="laboratory",
        coding=Coding(display=display),
        value=Quantity(value=value, unit=unit),
        report_id=report_id,
    )


def _component(code: str, value: float) -> ObservationComponent:
    return ObservationComponent(
        coding=Coding(code=code, display=code),
        value=Quantity(value=value, unit="mmHg"),
    )
