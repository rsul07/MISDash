"""Tests for generic backend metric series."""

from __future__ import annotations

from datetime import date, datetime

from src.backend.metrics import build_metric_series
from src.contracts.patient.v1 import Observation, ObservationComponent, Patient, PatientRecord
from src.contracts.patient.v1.common import Coding, Quantity, SourceReference


SOURCE = SourceReference(block="test")


def test_metric_projection_maps_components_and_laboratory_aliases() -> None:
    record = _record(
        Observation(
            id="bp-1",
            source=SOURCE,
            observed_at=datetime(2026, 1, 1, 8, 30),
            category="self-monitoring",
            coding=Coding(code="blood-pressure", display="АД"),
            components=[
                ObservationComponent(
                    coding=Coding(code="systolic", display="Систолическое АД"),
                    value=Quantity(value=140, unit="mmHg"),
                ),
                ObservationComponent(
                    coding=Coding(code="diastolic", display="Диастолическое АД"),
                    value=Quantity(value=90, unit="mmHg"),
                ),
            ],
        ),
        Observation(
            id="glucose-1",
            source=SOURCE,
            observed_at=date(2026, 1, 2),
            category="laboratory",
            coding=Coding(code="NSI.1", display="Глюкоза"),
            value=Quantity(value=6.5, unit="ммоль/л"),
        ),
    )

    metrics = {item.code: item for item in build_metric_series(record)}

    assert metrics["systolic"].points[0].value == 140
    assert metrics["diastolic"].points[0].value == 90
    assert metrics["glucose"].unit == "mmol/L"
    assert metrics["glucose"].points[0].value == 6.5


def test_metric_projection_excludes_urine_and_incompatible_units() -> None:
    record = _record(
        Observation(
            id="urine-glucose",
            source=SOURCE,
            observed_at=date(2026, 1, 1),
            category="laboratory",
            coding=Coding(display="Глюкоза мочи"),
            value=Quantity(value=10, unit="ммоль/л"),
        ),
        Observation(
            id="blood-glucose-mg",
            source=SOURCE,
            observed_at=date(2026, 1, 1),
            category="laboratory",
            coding=Coding(display="Глюкоза"),
            value=Quantity(value=120, unit="mg/dL"),
        ),
        Observation(
            id="unknown",
            source=SOURCE,
            observed_at=date(2026, 1, 1),
            category="laboratory",
            coding=Coding(display="Неизвестный показатель"),
            value=Quantity(value=42),
        ),
    )

    assert build_metric_series(record) == []


def test_metric_points_are_sorted_chronologically() -> None:
    record = _record(
        _scalar("new", date(2026, 2, 1), "body-weight", 82, "kg"),
        _scalar("old", date(2026, 1, 1), "body-weight", 80, "кг"),
    )

    series = build_metric_series(record)[0]

    assert series.code == "body-weight"
    assert [point.value for point in series.points] == [80, 82]


def _scalar(
    observation_id: str,
    observed_at: date,
    code: str,
    value: float,
    unit: str,
) -> Observation:
    return Observation(
        id=observation_id,
        source=SOURCE,
        observed_at=observed_at,
        category="vital-signs",
        coding=Coding(code=code, display=code),
        value=Quantity(value=value, unit=unit),
    )


def _record(*observations: Observation) -> PatientRecord:
    return PatientRecord(
        patient=Patient(id="patient-1", full_name="Пациент", source=SOURCE),
        observations=list(observations),
    )
