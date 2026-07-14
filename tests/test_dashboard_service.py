"""Integration tests for DashboardService and its storage boundary."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.backend import DashboardService
from src.contracts.patient.v1 import Encounter, Observation, Patient, PatientRecord
from src.contracts.patient.v1.common import Coding, Quantity, SourceReference
from src.storage import load_patient_record, save_patient_record


SOURCE = SourceReference(block="test")
GENERATED_AT = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def test_dashboard_service_builds_complete_frontend_response() -> None:
    response = DashboardService().build(
        _record(),
        as_of=date(2026, 7, 14),
        generated_at=GENERATED_AT,
    )

    assert response.schema_version == "1.0"
    assert response.generated_at == GENERATED_AT
    assert response.patient.full_name == "Иванов Иван"
    assert response.patient.age == 46
    assert response.metrics[0].code == "glucose"
    assert response.metrics[0].points[0].value == 6.5
    assert response.visits[0].id == "visit-1"
    assert response.red_flags == []
    assert response.ai_summary is None


def test_service_loads_canonical_record_from_json_boundary(tmp_path: Path) -> None:
    path = tmp_path / "patient_record.json"
    saved_path = save_patient_record(path, _record())

    loaded = load_patient_record(path)
    response = DashboardService().build_from_path(
        path,
        generated_at=GENERATED_AT,
    )

    assert saved_path == path
    assert loaded.patient.id == "patient-1"
    assert response.patient.id == "patient-1"
    assert response.model_dump(mode="json")["generated_at"].endswith("Z")
    assert not (tmp_path / "patient_record.json.tmp").exists()


def test_repository_reports_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid PatientRecord JSON"):
        load_patient_record(path)


def test_repository_rejects_invalid_contract(tmp_path: Path) -> None:
    path = tmp_path / "wrong-contract.json"
    path.write_text(
        json.dumps({"schema_version": "1.0", "patient": {"id": "missing"}}),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_patient_record(path)


def _record() -> PatientRecord:
    return PatientRecord(
        patient=Patient(
            id="patient-1",
            full_name="Иванов Иван",
            birth_date=date(1980, 3, 1),
            source=SOURCE,
        ),
        observations=[
            Observation(
                id="glucose-1",
                source=SOURCE,
                observed_at=date(2026, 7, 1),
                category="laboratory",
                coding=Coding(display="Глюкоза"),
                value=Quantity(value=6.5, unit="ммоль/л"),
            )
        ],
        encounters=[
            Encounter(
                id="visit-1",
                source=SOURCE,
                occurred_at=date(2026, 7, 2),
                complaints="жалоб нет",
            )
        ],
    )
