"""Construction of the dashboard visits contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .normalizers import clean_text, normalize_date
from .records import as_mapping, first, unique_visits


def build_visits(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    source = first(
        data,
        "PRIEMY_VRACHA",
        "priemy_vracha",
        "visits",
        "appointments",
    )
    rows: list[dict[str, Any]] = []
    for visit in unique_visits(source):
        doctor_data = first(visit, "VRACH", "vrach", "doctor", "physician")
        doctor_mapping = as_mapping(doctor_data)
        doctor = clean_text(
            first(doctor_mapping, "fio_doc", "FIO", "fio", "name", "doctor")
        )
        if not doctor:
            doctor = clean_text(doctor_data)
        specialty = clean_text(
            first(
                doctor_mapping,
                "spec_name",
                "specialty",
                "speciality",
                "specialization",
            )
        ) or clean_text(first(visit, "specialty", "spec_name"))

        diagnosis_data = first(
            visit,
            "diagnoz_priema",
            "diagnosis",
            "diagnoz",
            "visit_diagnosis",
        )
        diagnosis_mapping = as_mapping(diagnosis_data)
        diagnosis = clean_text(
            first(
                diagnosis_mapping,
                "osnovnoy_txt",
                "diagnosis",
                "diagnoz",
                "name",
                "osnovnoy_MKB",
                "code",
            )
        )
        if not diagnosis:
            diagnosis = clean_text(diagnosis_data)

        row = {
            "date": normalize_date(
                first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
            )
            or "",
            "doctor": doctor,
            "specialty": specialty,
            "diagnosis": diagnosis,
            "complaints": clean_text(
                first(visit, "JALOBY_TXT", "jaloby_txt", "complaints", "jaloby")
            ),
        }
        if any(row.values()):
            rows.append(row)
    rows.sort(key=lambda row: (not bool(row["date"]), row["date"]))
    return rows
