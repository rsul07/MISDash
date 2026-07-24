"""Tests for canonical encounter and medication adapters."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from src.parser.canonical.encounters import build_encounters


def test_encounter_adapter_preserves_full_clinical_visit() -> None:
    bundle = build_encounters(_etalon_data())

    assert len(bundle.encounters) == 81
    assert len(bundle.medications) == 373
    first = bundle.encounters[0]
    assert first.id == "VST-170602-578"
    assert first.occurred_at == date(2017, 6, 2)
    assert first.practitioner.name == "Шульц Е.В."
    assert first.practitioner.specialty == "эндокринолог"
    assert first.location == "128"
    assert first.complaints
    assert first.history
    assert first.objective
    assert first.plan
    assert len(first.diagnoses) == 5
    assert first.diagnoses[0].coding.code == "I11.9"
    assert first.diagnoses[1].coding.code == "E11.9"
    assert first.medication_ids == [
        "VST-170602-578-medication-1",
        "VST-170602-578-medication-2",
    ]
    assert bundle.medications[0].encounter_id == first.id
    assert bundle.medications[0].name == "Эналаприл"


def test_encounter_adapter_merges_duplicate_source_visits() -> None:
    data = {
        "PRIEMY_VRACHA": [
            {
                "id_priema": "visit_dup",
                "dt_priem": "01.03.2024 10:30",
                "JALOBY_TXT": "жалоба",
                "terapiya": [{"preparat": "Препарат", "doza": "5 мг"}],
            },
            {
                "id_priema": "visit",
                "dt_priem": "2024-03-01",
                "anamnez_txt": "анамнез",
                "obektivny_status": "статус",
                "naznacheniya_txt": "план",
                "VRACH": {"fio_doc": "Врач"},
                "diagnoz_priema": {"osnovnoy_MKB": "I10"},
            },
        ]
    }

    bundle = build_encounters(data)

    assert len(bundle.encounters) == 1
    assert bundle.encounters[0].id == "visit"
    assert bundle.encounters[0].occurred_at == datetime(2024, 3, 1, 10, 30)
    assert bundle.encounters[0].complaints == "жалоба"
    assert bundle.encounters[0].history == "анамнез"
    assert bundle.encounters[0].diagnoses[0].coding.display == "I10"
    assert bundle.encounters[0].medication_ids == ["visit-medication-1"]
    assert bundle.encounters[0].source.path == "PRIEMY_VRACHA[1]"
    assert bundle.encounters[0].source.source_id == "visit"
    assert bundle.medications[0].source.path == "PRIEMY_VRACHA[1].terapiya[0]"


def test_encounter_adapter_tolerates_wrong_source_types() -> None:
    assert build_encounters({"PRIEMY_VRACHA": "wrong"}).encounters == []
    assert build_encounters({"PRIEMY_VRACHA": [None, 42]}).medications == []


def _etalon_data() -> dict[str, object]:
    path = Path(__file__).parents[1] / "data" / "patient_etalon.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("data", payload)
