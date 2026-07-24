"""Tests for lossless canonical observation adapters."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.parser.canonical.observations import build_observations


def test_observations_preserve_each_etalon_measurement() -> None:
    bundle = build_observations(_etalon_data())

    categories = Counter(item.category for item in bundle.observations)
    assert len(bundle.observations) == 20_268
    assert categories == {
        "self-monitoring": 13_508,
        "laboratory": 6_293,
        "vital-signs": 467,
    }
    assert len(bundle.diagnostic_reports) == 1_416

    first_bp = bundle.observations[0]
    assert first_bp.observed_at == datetime(2020, 5, 20, 13, 47)
    assert first_bp.components[0].value.value == 155
    assert first_bp.components[1].value.value == 79
    assert first_bp.device == "OMRON-M3-8842"
    assert first_bp.context["period"] == "день"
    first_pulse = bundle.observations[1]
    assert first_pulse.coding.code == "heart-rate"
    assert first_pulse.value is not None
    assert first_pulse.value.value == 60


def test_laboratory_keeps_units_references_method_and_report_link() -> None:
    bundle = build_observations(_etalon_data())
    first_report = bundle.diagnostic_reports[0]
    first_result = next(
        item for item in bundle.observations if item.report_id == first_report.id
    )

    assert first_report.id == "LB700008"
    assert first_report.specimen == "кровь венозная"
    assert first_report.facility == "ЦКДЛ"
    assert first_result.coding.display == "МНО"
    assert first_result.value is not None
    assert first_result.value.value == 1.03
    assert first_result.reference_range is not None
    assert first_result.reference_range.low == 0.85
    assert first_result.reference_range.high == 1.15
    assert first_result.method == "ИФА"
    assert first_result.status == "final"
    assert first_result.id in first_report.observation_ids


def test_laboratory_preserves_clinical_result_comment() -> None:
    bundle = build_observations(
        {
            "lab_issledovaniya": [
                {
                    "nomer_zakaza": "lab-1",
                    "data_vzyatia": "2024-03-01",
                    "REZULTATY": [
                        {
                            "pokazatel": "Калий",
                            "REZULT": "5,4",
                            "comment_lab": "гемолиз, интерпретировать с осторожностью",
                        }
                    ],
                }
            ]
        }
    )

    result = bundle.observations[0]
    assert result.context == {
        "laboratory_comment": "гемолиз, интерпретировать с осторожностью"
    }


def test_direct_and_visit_observations_accept_dirty_shapes() -> None:
    data = {
        "vitals": {"v1": {"date": "01.03.2024", "glucose": "6,5"}},
        "PRIEMY_VRACHA": [
            {
                "id_priema": "visit-1",
                "dt_priem": "2024-03-01T10:30:00",
                "obektivny_status": "АД 140/90, ЧСС 72",
                "izmereniya": {"ves": "80,5", "SpO2": 98},
            }
        ],
    }

    bundle = build_observations(data)

    by_id = {item.id: item for item in bundle.observations}
    assert by_id["direct-1-glucose"].value is not None
    assert by_id["direct-1-glucose"].value.value == 6.5
    assert by_id["visit-1-blood-pressure"].method == "text-extraction"
    assert by_id["visit-1-heart-rate"].value is not None
    assert by_id["visit-1-heart-rate"].value.value == 72
    assert by_id["visit-1-body-weight"].value is not None
    assert by_id["visit-1-body-weight"].value.value == 80.5
    assert by_id["visit-1-oxygen-saturation"].value is not None


def test_visit_observation_source_path_survives_deduplication() -> None:
    data = {
        "PRIEMY_VRACHA": [
            {
                "id_priema": "visit-1_dup",
                "izmereniya": {"AD_sist": 140, "AD_diast": 90},
            },
            {
                "id_priema": "visit-1",
                "dt_priem": "2024-03-01",
                "izmereniya": {"CHSS": 72},
            },
        ]
    }

    bundle = build_observations(data)

    by_id = {item.id: item for item in bundle.observations}
    blood_pressure = by_id["visit-1-blood-pressure"]
    heart_rate = by_id["visit-1-heart-rate"]
    assert blood_pressure.source.path == "PRIEMY_VRACHA[1].izmereniya"
    assert blood_pressure.source.source_id == "visit-1"
    assert heart_rate.source.path == "PRIEMY_VRACHA[1].izmereniya"


def test_observation_adapters_tolerate_missing_blocks() -> None:
    bundle = build_observations(
        {
            "dnevnik_samokontrolya": "wrong",
            "lab_issledovaniya": None,
            "PRIEMY_VRACHA": [None, 42],
            "vitals": [],
        }
    )

    assert bundle.observations == []
    assert bundle.diagnostic_reports == []


def _etalon_data() -> dict[str, object]:
    path = Path(__file__).parents[1] / "data" / "patient_etalon.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("data", payload)
