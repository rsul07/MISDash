"""Tests for canonical patient and clinical-history adapters."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from src.parser.canonical.dates import parse_clinical_date
from src.parser.canonical.history import build_history
from src.parser.canonical.patient import build_patient


def test_parse_clinical_date_preserves_supported_precision() -> None:
    assert parse_clinical_date("2024-03-01") == date(2024, 3, 1)
    assert parse_clinical_date("01.03.2024 18:45") == datetime(
        2024, 3, 1, 18, 45
    )
    assert parse_clinical_date("1709251200") == datetime(
        2024, 3, 1, tzinfo=timezone.utc
    )
    assert parse_clinical_date("2017") is None
    assert parse_clinical_date("1984 г.") is None


def test_patient_adapter_maps_identity_allergies_and_conditions() -> None:
    data = _etalon_data()

    bundle = build_patient(data)

    assert bundle.patient.id == "0004512-К"
    assert bundle.patient.full_name == "Симаков Виктор Геннадьевич"
    assert bundle.patient.birth_date == date(1967, 3, 14)
    assert bundle.patient.gender == "male"
    assert bundle.patient.height_cm == 176
    assert len(bundle.allergies) == 2
    assert bundle.allergies[0].agent == "Пенициллин"
    assert bundle.allergies[0].onset_year == 1989
    assert len(bundle.conditions) == 6
    assert bundle.conditions[0].coding.code == "I11.9"
    assert bundle.conditions[2].onset == datetime(
        2022, 5, 20, tzinfo=timezone.utc
    )


def test_history_adapter_keeps_events_and_imprecise_dates() -> None:
    history = build_history(_etalon_data())

    assert len(history.procedures) == 2
    assert history.procedures[0].performed_at is None
    assert history.procedures[0].performed_at_text == "1984 г."
    assert len(history.hospitalizations) == 2
    assert history.hospitalizations[1].admitted_at == datetime(
        2025, 3, 16, tzinfo=timezone.utc
    )
    assert len(history.immunizations) == 3
    assert history.immunizations[2].administered_at is None
    assert history.immunizations[2].administered_at_text == "2017"
    assert len(history.diagnostic_reports) == 36
    assert history.diagnostic_reports[0].source.source_id == "FD-44716"
    assert history.diagnostic_reports[0].conclusion


def test_adapters_tolerate_missing_or_wrong_type_blocks() -> None:
    data = {
        "PATIENT_INFO": [],
        "social_anamnez": "wrong",
        "hron_zabolevaniya": None,
        "perenesennye_operacii": 42,
        "gospitalizacii": "wrong",
        "privivki": None,
        "instrumental_issled": [],
    }

    patient = build_patient(data)
    history = build_history(data)

    assert patient.patient.id == "patient"
    assert patient.patient.full_name == ""
    assert patient.allergies == []
    assert patient.conditions == []
    assert history.procedures == []
    assert history.hospitalizations == []
    assert history.immunizations == []
    assert history.diagnostic_reports == []


def _etalon_data() -> dict[str, object]:
    path = Path(__file__).parents[1] / "data" / "patient_etalon.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("data", payload)
