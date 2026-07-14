"""Tests for dashboard profile and visit projections."""

from __future__ import annotations

from datetime import date, datetime

from src.backend.profile import build_profile_projection
from src.backend.visits import build_visit_summaries
from src.contracts.patient.v1 import (
    Encounter,
    Medication,
    Observation,
    Patient,
    PatientRecord,
)
from src.contracts.patient.v1.common import Coding, Quantity, SourceReference


SOURCE = SourceReference(block="test")


def test_profile_uses_latest_measurements_and_medications() -> None:
    record = _record()

    projection = build_profile_projection(record, as_of=date(2026, 7, 14))

    assert projection.patient.age == 46
    assert projection.patient.height_cm == 180
    assert projection.patient.last_weight_kg == 90
    assert projection.patient.bmi == 27.8
    assert [item.name for item in projection.current_medications] == ["Препарат Б"]


def test_visit_projection_is_recent_first_and_keeps_stable_fields() -> None:
    visits = build_visit_summaries(_record())

    assert [item.id for item in visits] == ["visit-2", "visit-1"]
    assert visits[0].practitioner == "Петров П.П."
    assert visits[0].specialty == "терапевт"
    assert visits[0].diagnoses[0].code == "I10"
    assert visits[0].complaints == "головная боль"


def test_profile_handles_missing_measurements_and_future_birth_date() -> None:
    record = PatientRecord(
        patient=Patient(
            id="patient-2",
            full_name="Нет данных",
            birth_date=date(2030, 1, 1),
            source=SOURCE,
        )
    )

    projection = build_profile_projection(record, as_of=date(2026, 1, 1))

    assert projection.patient.age is None
    assert projection.patient.bmi is None
    assert projection.current_medications == []
    assert build_visit_summaries(record) == []


def _record() -> PatientRecord:
    medication_a = Medication(
        id="medication-a",
        source=SOURCE,
        name="Препарат А",
        encounter_id="visit-1",
    )
    medication_b = Medication(
        id="medication-b",
        source=SOURCE,
        name="Препарат Б",
        encounter_id="visit-2",
    )
    encounters = [
        Encounter(
            id="visit-1",
            source=SOURCE,
            occurred_at=date(2025, 1, 1),
            medication_ids=[medication_a.id],
        ),
        Encounter(
            id="visit-2",
            source=SOURCE,
            occurred_at=datetime(2026, 1, 1, 10, 30),
            practitioner={"name": "Петров П.П.", "specialty": "терапевт"},
            diagnoses=[
                {"coding": {"code": "I10", "display": "Гипертензия"}}
            ],
            complaints="головная боль",
            medication_ids=[medication_b.id],
        ),
    ]
    observations = [
        Observation(
            id="weight-old",
            source=SOURCE,
            observed_at=date(2025, 1, 1),
            category="vital-signs",
            coding=Coding(code="body-weight", display="Масса тела"),
            value=Quantity(value=80, unit="kg"),
        ),
        Observation(
            id="weight-new",
            source=SOURCE,
            observed_at=date(2026, 1, 1),
            category="vital-signs",
            coding=Coding(code="body-weight", display="Масса тела"),
            value=Quantity(value=90, unit="kg"),
        ),
    ]
    return PatientRecord(
        patient=Patient(
            id="patient-1",
            full_name="Иванов Иван",
            birth_date=date(1980, 3, 1),
            height_cm=180,
            last_weight_kg=70,
            source=SOURCE,
        ),
        medications=[medication_a, medication_b],
        encounters=encounters,
        observations=observations,
    )
