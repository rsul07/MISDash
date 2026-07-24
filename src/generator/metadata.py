"""Duplicate event logs, migration artifacts, and service noise."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any


def build_metadata(
    rnd: random.Random,
    end: datetime,
    visits: list[dict[str, Any]],
    labs: list[dict[str, Any]],
    instrumental: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Build derived noisy sections without changing RNG call order."""

    events: list[dict[str, Any]] = []
    event_id = 5_000_000

    def add_event(
        date_text: str,
        event_type: str,
        reference: str,
        text: str,
    ) -> None:
        nonlocal event_id
        event_id += rnd.randint(3, 40)
        events.append(
            {
                "EVENT_ID": event_id,
                "EVENT_TYPE": event_type,
                "EVENT_DT": date_text,
                "REF_ID": reference,
                "PAT_ID": "0004512-К",
                "SHORT_TXT": text[:120],
                "USER_CREATE": rnd.choice(
                    [
                        "system_import",
                        "reg_petrova",
                        "dr_kovaleva",
                        "kdl_auto",
                    ]
                ),
                "IS_ACTUAL": 1,
                "VERSION": rnd.randint(1, 3),
            }
        )

    for visit in visits:
        add_event(
            visit["dt_priem"],
            "AMB_VISIT",
            visit["id_priema"],
            "Приём: "
            + visit["VRACH"]["spec_name"]
            + ". "
            + visit["JALOBY_TXT"],
        )
    for laboratory in labs:
        add_event(
            laboratory["data_gotovnosti"],
            "LAB_RESULT",
            laboratory["nomer_zakaza"],
            "Готов результат: " + laboratory["gruppa_issled_name"],
        )
    for investigation in instrumental:
        add_event(
            investigation["DT_ISSLED"],
            "FUNC_DIAG",
            investigation["protokol_id"],
            investigation["issledovanie"]
            + ": "
            + investigation["zakluchenie_txt"],
        )

    legacy: dict[str, Any] = {
        "_comment": (
            "MIGRATED FROM KVAZAR v3.1 — DO NOT USE "
            "(см. tmp_flags.migrated_from_v3)"
        ),
        "records": [],
    }
    for visit in visits[: int(len(visits) * 0.8)]:
        legacy["records"].append(
            {
                "REC_TYPE": "PRIEM",
                "REC_DT": visit["dt_priem"],
                "DOC": visit["VRACH"]["fio_doc"],
                "TXT_FULL": " | ".join(
                    [
                        "ЖАЛОБЫ: " + visit["JALOBY_TXT"],
                        "АНАМНЕЗ: " + visit["anamnez_txt"],
                        "СТАТУС: " + visit["obektivny_status"],
                        "НАЗНАЧЕНО: " + visit["naznacheniya_txt"],
                    ]
                ),
                "OLD_ID": rnd.randint(100000, 999999),
            }
        )
    for laboratory in labs[: int(len(labs) * 0.85)]:
        for result in laboratory["REZULTATY"]:
            legacy["records"].append(
                {
                    "REC_TYPE": "LAB",
                    "REC_DT": laboratory["data_vzyatia"],
                    "ANALIT": result["pokazatel"],
                    "VAL": result["REZULT"],
                    "ED": result.get("ed_izm"),
                    "NORMA": result.get("referens"),
                    "OLD_ID": rnd.randint(100000, 999999),
                }
            )

    service_noise = {
        "sys_info": {
            "mis_name": "МИС «Квазар-Мед» v4.2.117",
            "export_dt": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "export_user": "ivanova_ei",
            "schema_ver": "2.11",
            "encoding": "utf-8",
        },
        "EMPTY_BLOCK_RESERVED": {},
        "tmp_flags": {
            "f1": 0,
            "f2": 0,
            "f3": None,
            "migrated_from_v3": True,
            "unresolved_conflicts": [
                "ves_kg_last vs izmereniya.ves за 2025-11",
                "дубль аллергии на пенициллин",
            ],
        },
        "documents_attached": [
            {
                "doc_type": "выписка из стационара",
                "file": "scan_20191119_0012.pdf",
                "raspoznan": 0,
            },
            {
                "doc_type": "результаты МРТ (внешн.)",
                "file": "IMG_4482.jpg",
                "raspoznan": 0,
                "prim": "принесён пациентом, в карту не разнесён",
            },
        ],
    }
    return events, legacy, service_noise
