"""Tests for the public fault-tolerant MIS parser facade."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.parser.engine import (
    MISParser,
    extract_vitals_from_text,
    normalize_date,
    parse_number,
)
from src.parser.records import first


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2024-03-01", "2024-03-01"),
        ("01.03.2024", "2024-03-01"),
        ("01/03/2024", "2024-03-01"),
        ("01/03/24", "2024-03-01"),
        ("20240301", "2024-03-01"),
        (20240301, "2024-03-01"),
        ("2024-03-01T18:45:00", "2024-03-01"),
        ("01.03.2024 18:45", "2024-03-01"),
        (1709251200, "2024-03-01"),
        ("1709251200", "2024-03-01"),
        (0, "1970-01-01"),
        ("-1", "1969-12-31"),
        (2017, None),
        (None, None),
        ("31.02.2024", None),
        ({"date": "2024-03-01"}, None),
    ],
)
def test_normalize_date(raw: object, expected: str | None) -> None:
    assert normalize_date(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("46,5", 46.5),
        (" 46,5 ", 46.5),
        (46, 46.0),
        (0, 0.0),
        (None, None),
        (True, None),
        ("н/д", None),
        ("46,5 кг", None),
        (float("inf"), None),
    ],
)
def test_parse_number(raw: object, expected: float | None) -> None:
    assert parse_number(raw) == expected


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_first_skips_non_finite_values_and_uses_fallback(non_finite: float) -> None:
    payload = {"preferred": non_finite, "fallback": "usable"}

    assert first(payload, "preferred", "fallback") == "usable"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "ЧСС 67 в мин. АД 144/75 мм рт.ст.",
            {"sys_bp": 144, "dia_bp": 75, "heart_rate": 67},
        ),
        (
            "Пульс: 71. АД на правой руке 149/85.",
            {"sys_bp": 149, "dia_bp": 85, "heart_rate": 71},
        ),
        (
            "АД 80/120 ошибочно; затем А/Д 125-82, HR 68",
            {"sys_bp": 125, "dia_bp": 82, "heart_rate": 68},
        ),
        (None, {"sys_bp": None, "dia_bp": None, "heart_rate": None}),
    ],
)
def test_extract_vitals_from_text(
    text: object,
    expected: dict[str, int | None],
) -> None:
    assert extract_vitals_from_text(text) == expected


def test_parse_record_builds_canonical_model_without_writing(tmp_path: Path) -> None:
    source = _write_dirty_patient(tmp_path)
    output = tmp_path / "must-not-exist"

    record = MISParser(source, output_dir=output).parse_record()

    assert not output.exists()
    assert record.schema_version == "1.0"
    assert record.patient.full_name == "Иванов Иван Иванович"
    assert len(record.allergies) == 1
    assert len(record.conditions) == 1
    assert len(record.encounters) == 1
    assert record.encounters[0].objective == "ЧСС 72. АД 150/90."
    assert record.medications[0].name == "Лозартан"
    assert len(record.observations) == 7
    assert len(record.diagnostic_reports) == 1


def test_parse_persists_only_patient_record(tmp_path: Path) -> None:
    source = _write_dirty_patient(tmp_path)
    output = tmp_path / "output"

    paths = MISParser(source, output_dir=output).parse()

    assert paths == {"patient_record": output / "patient_record.json"}
    assert [item.name for item in output.iterdir()] == ["patient_record.json"]
    payload = json.loads(paths["patient_record"].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["patient"]["id"] == "patient-1"


def test_missing_and_wrong_type_blocks_produce_empty_collections(
    tmp_path: Path,
) -> None:
    source = tmp_path / "missing.json"
    source.write_text(
        json.dumps(
            {
                "data": {
                    "PATIENT_INFO": [],
                    "social_anamnez": "wrong",
                    "hron_zabolevaniya": 42,
                    "PRIEMY_VRACHA": [None, "wrong", {"VRACH": None}],
                    "lab_issledovaniya": None,
                    "dnevnik_samokontrolya": [],
                    "instrumental_issled": "wrong",
                }
            }
        ),
        encoding="utf-8",
    )

    record = MISParser(source).parse_record()

    assert record.patient.id == "patient"
    assert record.allergies == []
    assert record.observations == []
    assert len(record.encounters) == 1


def test_invalid_json_has_contextual_error(tmp_path: Path) -> None:
    source = tmp_path / "broken.json"
    source.write_text("{broken", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON in"):
        MISParser(source).parse_record()


def test_output_dir_is_read_from_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "patient.json"
    source.write_text("{}", encoding="utf-8")
    configured_output = tmp_path / "from-env"
    monkeypatch.setenv("OUTPUT_DIR", str(configured_output))

    paths = MISParser(source).run()

    assert paths == {"patient_record": configured_output / "patient_record.json"}


def _write_dirty_patient(tmp_path: Path) -> Path:
    source = tmp_path / "patient.json"
    payload = {
        "data": {
            "PATIENT_INFO": {
                "pat_id": "patient-1",
                "FIO": "ИВАНОВ ИВАН ИВАНОВИЧ",
                "DATE_ROJD": "01/03/1980",
                "rost_sm": "180",
                "ves_kg_last": "81,0",
            },
            "social_anamnez": {
                "allergoanamnez": [
                    {"agent": "Пенициллин", "reakciya": "сыпь"},
                    {"agent": "Пенициллины", "note": "дубль записи"},
                ]
            },
            "hron_zabolevaniya": [
                {"MKB10_KOD": "I10", "DIAGNOZ_NAME": "Гипертония"}
            ],
            "dnevnik_samokontrolya": {
                "AD_izmereniya": [
                    {"dt": "01.03.2024 08:00", "sys": 140, "dia": 90, "pulse": 70}
                ],
                "glikemiya": [
                    {"izmereno": "01.03.2024", "glukoza_mmol": "6,4"}
                ],
            },
            "lab_issledovaniya": [
                {
                    "nomer_zakaza": "lab-1",
                    "data_vzyatia": "2024-03-01",
                    "REZULTATY": [
                        {"pokazatel": "HbA1c", "REZULT": "7,1", "ed_izm": "%"}
                    ],
                }
            ],
            "PRIEMY_VRACHA": [
                {
                    "id_priema": "visit-1",
                    "dt_priem": "01.03.2024",
                    "obektivny_status": "ЧСС 72. АД 150/90.",
                    "izmereniya": {"ves": "80,5"},
                    "terapiya": [{"preparat": "Лозартан", "doza": "50 мг"}],
                },
                {"id_priema": "visit-1_dup", "JALOBY_TXT": "дубль"},
            ],
        }
    }
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return source
