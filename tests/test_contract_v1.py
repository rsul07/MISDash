"""Executable specification for the PatientRecord v1 contract."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.contracts.patient.v1 import (
    Encounter,
    Observation,
    ObservationComponent,
    Patient,
    PatientRecord,
)
from src.contracts.patient.v1.common import Coding, Quantity, SourceReference


def test_patient_record_serializes_as_versioned_backend_contract() -> None:
    source = SourceReference(block="PATIENT_INFO", source_id="patient-1")
    patient = Patient(
        id="patient-1",
        full_name="Иванов Иван Иванович",
        birth_date=date(1980, 3, 1),
        gender="male",
        source=source,
    )
    encounter = Encounter(
        id="visit-1",
        source=SourceReference(block="PRIEMY_VRACHA", source_id="visit-1"),
        occurred_at=datetime(2024, 1, 2, 10, 30),
        complaints="головная боль",
    )
    observation = Observation(
        id="bp-1",
        source=SourceReference(block="PRIEMY_VRACHA", source_id="visit-1"),
        observed_at=datetime(2024, 1, 2, 10, 30),
        category="vital-signs",
        coding=Coding(code="blood-pressure", display="Артериальное давление"),
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
        encounter_id="visit-1",
    )

    record = PatientRecord(
        patient=patient,
        encounters=[encounter],
        observations=[observation],
    )
    payload = record.model_dump(mode="json")

    assert payload["schema_version"] == "1.0"
    assert payload["patient"]["birth_date"] == "1980-03-01"
    assert payload["encounters"][0]["occurred_at"] == "2024-01-02T10:30:00"
    assert payload["observations"][0]["components"][0]["value"] == {
        "value": 140.0,
        "unit": "mmHg",
    }


def test_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Patient(
            id="patient-1",
            full_name="Иванов Иван",
            source=SourceReference(block="PATIENT_INFO"),
            raw_mis_field="must not leak into backend contract",
        )


def test_contract_rejects_unknown_schema_version() -> None:
    patient = Patient(
        id="patient-1",
        full_name="Иванов Иван",
        source=SourceReference(block="PATIENT_INFO"),
    )

    with pytest.raises(ValidationError):
        PatientRecord(schema_version="2.0", patient=patient)
