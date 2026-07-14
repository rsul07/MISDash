"""Tests for the fault-tolerant MIS parser."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from src.parser.engine import (
    MISParser,
    PROFILE_FIELDS,
    VISITS_FIELDS,
    VITALS_FIELDS,
    extract_vitals_from_text,
    normalize_date,
    parse_number,
)


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
        (86400, "1970-01-02"),
        ("86400", "1970-01-02"),
        (0, "1970-01-01"),
        ("0", "1970-01-01"),
        ("-1", "1969-12-31"),
        (2017, None),
        ("2017", None),
        (None, None),
        ("", None),
        ("-", None),
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
        ("46.5", 46.5),
        (46, 46.0),
        (0, 0.0),
        (None, None),
        (True, None),
        ("н/д", None),
        ("46,5 кг", None),
        ([46.5], None),
        (float("inf"), None),
    ],
)
def test_parse_number(raw: object, expected: float | None) -> None:
    assert parse_number(raw) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "ЧСС 67 в мин. АД 144/75 мм рт.ст.",
            {"sys_bp": 144, "dia_bp": 75, "heart_rate": 67},
        ),
        (
            "ЧСС 75 уд/мин, АД 130/89.",
            {"sys_bp": 130, "dia_bp": 89, "heart_rate": 75},
        ),
        (
            "Пульс: 71. АД на правой руке 149/85.",
            {"sys_bp": 149, "dia_bp": 85, "heart_rate": 71},
        ),
        (
            "повышение ад до 154/101 мм рт.ст.",
            {"sys_bp": 154, "dia_bp": 101, "heart_rate": None},
        ),
        (
            "АД 80/120 ошибочно; затем А/Д 125-82, HR 68",
            {"sys_bp": 125, "dia_bp": 82, "heart_rate": 68},
        ),
        (
            "Давление 132 на 84, пульс 74",
            {"sys_bp": 132, "dia_bp": 84, "heart_rate": 74},
        ),
        (
            None,
            {"sys_bp": None, "dia_bp": None, "heart_rate": None},
        ),
    ],
)
def test_extract_vitals_from_text(
    text: object, expected: dict[str, int | None]
) -> None:
    assert extract_vitals_from_text(text) == expected


def test_parser_writes_contract_files_from_dirty_data(tmp_path: Path) -> None:
    source = tmp_path / "patient.json"
    output = tmp_path / "nested" / "output"
    payload = {
        "result": {"code": 0},
        "data": {
            "PATIENT_INFO": {
                "FIO": "ИВАНОВ ИВАН ИВАНОВИЧ",
                "birht_date": "-",
                "DATE_ROJD": "01/03/1980",
                "pol": "м",
                "blood_grp": "A(II) Rh+",
                "rost_sm": "180",
                "ves_kg_last": "81,0",
            },
            "social_anamnez": {
                "allergoanamnez": [
                    {"agent": "Пенициллин", "reakciya": "сыпь"},
                    {"AGENT_NAME": "Латекс", "react": "зуд"},
                    {
                        "AGENT_NAME": "Пенициллины",
                        "react": "сыпь",
                        "note": "дубль записи",
                    },
                ]
            },
            "hron_zabolevaniya": [
                {"DIAGNOZ_NAME": "Гипертоническая болезнь"}
            ],
            "dnevnik_samokontrolya": {
                "glikemiya": [
                    {"izmereno": "01.03.2024", "glukoza_mmol": "6,4"}
                ]
            },
            "lab_issledovaniya": [
                {
                    "data_vzyatia": "2024-03-01",
                    "REZULTATY": [
                        {"pokazatel": "Глюкоза", "REZULT": "6,5"},
                        {"pokazatel": "HbA1c", "REZULT": "7,1"},
                        {"pokazatel": "Креатинин", "REZULT": "101,2"},
                        {
                            "pokazatel": "Холестерин общий",
                            "REZULT": "5,8",
                        },
                    ],
                }
            ],
            "PRIEMY_VRACHA": [
                {
                    "id_priema": "visit-1",
                    "dt_priem": "01.03.2024",
                    "VRACH": {
                        "fio_doc": "Петров П.П.",
                        "spec_name": "терапевт",
                    },
                    "JALOBY_TXT": "головная боль, тошнота; АД до 170/100",
                    "obektivny_status": "ЧСС 72 в мин. АД 150/90 мм рт.ст.",
                    "izmereniya": {
                        "AD_sist": "140",
                        "AD_diast": None,
                        "CHSS": "-",
                        "ves": "80,5",
                    },
                    "diagnoz_priema": {"osnovnoy_txt": "Гипертония"},
                    "terapiya": [
                        {"preparat": "Лозартан", "doza": "50 мг", "krat": "1 р/сут"}
                    ],
                },
                {
                    "id_priema": "visit-1_dup",
                    "dt_priem": "2024-03-01",
                    "VRACH": {
                        "fio_doc": "Петров П.П.",
                        "spec_name": "терапевт",
                    },
                    "JALOBY_TXT": "головная боль, тошнота; АД до 170/100",
                    "diagnoz_priema": {"osnovnoy_txt": "Гипертония"},
                },
            ],
        },
    }
    # An incomplete duplicate appears first; the parser must still select the
    # more complete original record rather than relying on input order.
    payload["data"]["PRIEMY_VRACHA"].reverse()
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    paths = MISParser(source, output_dir=output).parse()

    assert set(paths) == {"profile", "vitals", "visits", "patient_record"}
    assert all(path.is_file() for path in paths.values())

    profile = json.loads(paths["profile"].read_text(encoding="utf-8"))
    assert tuple(profile) == PROFILE_FIELDS
    assert profile["fio"] == "Иванов Иван Иванович"
    assert profile["birth_date"] == "1980-03-01"
    assert profile["gender"] == "Мужской"
    assert profile["bmi"] == 25.0
    assert profile["allergies"] == ["Пенициллин (сыпь)", "Латекс (зуд)"]
    assert profile["chronic_diseases"] == ["Гипертоническая болезнь"]
    assert profile["current_therapy"] == ["Лозартан 50 мг 1 р/сут"]

    vitals = _read_csv(paths["vitals"])
    assert tuple(vitals[0]) == VITALS_FIELDS
    assert vitals == [
        {
            "date": "2024-03-01",
            "sys_bp": "150",
            "dia_bp": "90",
            "heart_rate": "72",
            "weight": "80.5",
            "glucose": "6.5",
            "hba1c": "7.1",
            "creatinine": "101.2",
            "cholesterol": "5.8",
        }
    ]

    visits = _read_csv(paths["visits"])
    assert tuple(visits[0]) == VISITS_FIELDS
    assert len(visits) == 1
    assert visits[0]["complaints"] == "головная боль, тошнота; АД до 170/100"

    patient_record = json.loads(
        paths["patient_record"].read_text(encoding="utf-8")
    )
    assert patient_record["schema_version"] == "1.0"
    assert patient_record["patient"]["full_name"] == "Иванов Иван Иванович"
    assert patient_record["social_history"] is None
    assert patient_record["family_history"] == []
    assert len(patient_record["encounters"]) == 1
    assert patient_record["encounters"][0]["history"] is None
    assert patient_record["encounters"][0]["objective"].startswith("ЧСС 72")
    assert patient_record["medications"][0]["name"] == "Лозартан"
    assert len(patient_record["observations"]) == 8
    assert len(patient_record["diagnostic_reports"]) == 1


def test_missing_and_wrong_type_blocks_produce_empty_contracts(tmp_path: Path) -> None:
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
                    "instrumental_issled": "missing is allowed",
                }
            }
        ),
        encoding="utf-8",
    )

    paths = MISParser(source, output_dir=tmp_path / "output").parse()
    profile = json.loads(paths["profile"].read_text(encoding="utf-8"))

    assert tuple(profile) == PROFILE_FIELDS
    assert profile == {
        "fio": "",
        "birth_date": "",
        "age": None,
        "gender": "",
        "blood_group": "",
        "bmi": None,
        "allergies": [],
        "chronic_diseases": [],
        "current_therapy": [],
    }
    patient_record = json.loads(
        paths["patient_record"].read_text(encoding="utf-8")
    )
    assert patient_record["patient"]["id"] == "patient"
    assert patient_record["allergies"] == []
    assert patient_record["observations"] == []
    assert paths["vitals"].read_text(encoding="utf-8").strip() == ",".join(
        VITALS_FIELDS
    )
    with paths["visits"].open(encoding="utf-8", newline="") as source_file:
        reader = csv.DictReader(source_file)
        assert tuple(reader.fieldnames or ()) == VISITS_FIELDS
        assert list(reader) == []


def test_vitals_are_averaged_per_day_with_source_priority(tmp_path: Path) -> None:
    source = tmp_path / "measurements.json"
    source.write_text(
        json.dumps(
            {
                "data": {
                    "dnevnik_samokontrolya": {
                        "AD_izmereniya": [
                            {
                                "dt": "2024-01-01T08:00:00",
                                "sys": 120,
                                "dia": 80,
                                "pulse": 60,
                            },
                            {
                                "dt": "2024-01-01T20:00:00",
                                "sys": 140,
                                "dia": 90,
                                "pulse": 80,
                            },
                        ],
                        "glikemiya": [
                            {
                                "izmereno": "2024-01-01T08:00:00",
                                "glukoza_mmol": "6,0",
                            },
                            {
                                "izmereno": "2024-01-01T20:00:00",
                                "glukoza_mmol": "8,0",
                            },
                        ],
                    },
                    "lab_issledovaniya": [
                        {
                            "data_vzyatia": "2024-01-02",
                            "REZULTATY": [
                                {"pokazatel": "Глюкоза крови", "REZULT": "10,0"},
                                {"pokazatel": "Глюкоза", "REZULT": "12,0"},
                            ],
                        }
                    ],
                    "vitals": [
                        {"date": "2024-01-01", "heart_rate": 1}
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    paths = MISParser(source, output_dir=tmp_path / "output").parse()

    vitals = _read_csv(paths["vitals"])
    assert vitals[0] == {
        "date": "2024-01-01",
        "sys_bp": "130",
        "dia_bp": "85",
        "heart_rate": "70",
        "weight": "",
        "glucose": "7.0",
        "hba1c": "",
        "creatinine": "",
        "cholesterol": "",
    }
    assert vitals[1]["date"] == "2024-01-02"
    assert vitals[1]["glucose"] == "11.0"


def test_single_visit_mapping_is_not_split_into_nested_records(tmp_path: Path) -> None:
    source = tmp_path / "single-visit.json"
    source.write_text(
        json.dumps(
            {
                "data": {
                    "PRIEMY_VRACHA": {
                        "VRACH": {"fio_doc": "Петров П.П."},
                        "diagnoz_priema": {"osnovnoy_txt": "Гипертония"},
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    paths = MISParser(source, output_dir=tmp_path / "output").parse()

    assert _read_csv(paths["visits"]) == [
        {
            "date": "",
            "doctor": "Петров П.П.",
            "specialty": "",
            "diagnosis": "Гипертония",
            "complaints": "",
        }
    ]


def test_keyed_mappings_are_treated_as_record_collections(tmp_path: Path) -> None:
    source = tmp_path / "keyed-records.json"
    source.write_text(
        json.dumps(
            {
                "data": {
                    "PRIEMY_VRACHA": {
                        "v1": {"id_priema": "v1", "dt_priem": "2024-01-01"},
                        "v2": {"id_priema": "v2", "dt_priem": "2024-01-02"},
                    },
                    "lab_issledovaniya": {
                        "panel-1": {
                            "data_vzyatia": "2024-01-01",
                            "REZULTATY": {
                                "result-1": {
                                    "pokazatel": "Креатинин",
                                    "REZULT": "95,5",
                                }
                            },
                        }
                    },
                    "dnevnik_samokontrolya": {
                        "AD_izmereniya": {
                            "bp-1": {
                                "dt": "2024-01-01",
                                "sys": 130,
                                "dia": 80,
                                "pulse": 70,
                            }
                        }
                    },
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    paths = MISParser(source, output_dir=tmp_path / "output").parse()

    assert [row["date"] for row in _read_csv(paths["visits"])] == [
        "2024-01-01",
        "2024-01-02",
    ]
    vitals = _read_csv(paths["vitals"])
    assert vitals[0]["sys_bp"] == "130"
    assert vitals[0]["creatinine"] == "95.5"


def test_duplicate_visits_merge_complementary_fields(tmp_path: Path) -> None:
    source = tmp_path / "complementary-duplicates.json"
    duplicate = {
        "id_priema": "visit_dup",
        "dt_priem": "2024-01-01",
        "VRACH": {"fio_doc": "Петров П.П.", "spec_name": "терапевт"},
        "JALOBY_TXT": "головная боль",
        "terapiya": [
            {"preparat": f"Препарат {index}", "doza": "1 мг"}
            for index in range(4)
        ],
    }
    original = {
        "id_priema": "visit",
        "dt_priem": "2024-01-01",
        "izmereniya": {"AD_sist": 140, "AD_diast": 90, "CHSS": 72},
    }
    source.write_text(
        json.dumps(
            {"data": {"PRIEMY_VRACHA": [duplicate, original]}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    paths = MISParser(source, output_dir=tmp_path / "output").parse()

    assert len(_read_csv(paths["visits"])) == 1
    assert _read_csv(paths["vitals"])[0]["sys_bp"] == "140"


def test_output_dir_is_read_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "patient.json"
    source.write_text("{}", encoding="utf-8")
    configured_output = tmp_path / "from-env"
    monkeypatch.setenv("OUTPUT_DIR", str(configured_output))

    paths = MISParser(source).run()

    assert all(path.parent == configured_output for path in paths.values())


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))
