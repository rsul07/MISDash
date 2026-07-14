"""Patient profile construction from normalized MIS records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .normalizers import (
    age_from_values,
    clean_name,
    clean_text,
    normalize_date,
    normalize_gender,
    parse_number,
)
from .records import (
    as_mapping,
    deduplicate,
    first,
    items,
    truthy_flag,
    unique_visits,
)


def build_profile(data: Mapping[str, Any]) -> dict[str, Any]:
    patient = as_mapping(first(data, "PATIENT_INFO", "patient_info", "patient", "profile"))
    visits = unique_visits(
        first(data, "PRIEMY_VRACHA", "priemy_vracha", "visits", "appointments")
    )

    fio = clean_name(first(patient, "FIO", "fio", "full_name", "name"))
    if not fio:
        fio = clean_name(
            " ".join(
                part
                for part in (
                    clean_text(first(patient, "pat_fam", "last_name")),
                    clean_text(first(patient, "pat_im", "first_name")),
                    clean_text(first(patient, "pat_otch", "middle_name")),
                )
                if part
            )
        )

    birth_date = normalize_date(
        first(
            patient,
            "birht_date",
            "birtf_date",
            "birth_date",
            "DATE_ROJD",
            "date_rojd",
        )
    )
    age = age_from_values(first(patient, "age", "vozrast"), birth_date)
    gender = normalize_gender(
        first(patient, "gender", "sex", "pol", "SEX_ID", "sex_id")
    )
    blood_group = clean_text(
        first(patient, "blood_grp", "blood_group", "gruppa_krovi")
    )

    bmi = parse_number(first(patient, "bmi", "BMI", "IMT", "imt"))
    if bmi is None:
        height = parse_number(first(patient, "rost_sm", "height", "height_cm", "rost"))
        weight = parse_number(
            first(patient, "ves_kg_last", "weight", "weight_kg", "ves")
        )
        if weight is None:
            weight = _latest_visit_measurement(visits, "ves", "weight", "weight_kg")
        if height is None:
            height = _latest_visit_measurement(visits, "rost", "height", "height_cm")
        if weight is not None and height is not None and height > 0:
            bmi = weight / ((height / 100) ** 2)
    if bmi is not None:
        bmi = round(bmi, 1)

    social = as_mapping(
        first(data, "social_anamnez", "social_history", "social_anamnesis")
    )
    allergies_source = first(
        social,
        "allergoanamnez",
        "allergies",
        "allergy_history",
    )
    if allergies_source is None:
        allergies_source = first(patient, "allergies", "allergoanamnez")

    chronic_source = first(
        data,
        "hron_zabolevaniya",
        "chronic_diseases",
        "chronic_conditions",
    )
    current_therapy = format_therapy(
        first(patient, "current_therapy", "terapiya", "therapy")
    )
    if not current_therapy:
        current_therapy = _latest_therapy(visits)

    return {
        "fio": fio,
        "birth_date": birth_date or "",
        "age": age,
        "gender": gender,
        "blood_group": blood_group,
        "bmi": bmi,
        "allergies": _extract_allergies(allergies_source),
        "chronic_diseases": _extract_chronic_diseases(chronic_source),
        "current_therapy": current_therapy,
    }


def _extract_allergies(source: Any) -> list[str]:
    allergies: list[str] = []
    for record in items(source):
        if isinstance(record, Mapping):
            note = clean_text(first(record, "note", "prim", "comment", "description"))
            if "дубл" in note.casefold() or truthy_flag(
                first(record, "is_deleted", "deleted")
            ):
                continue
            agent = clean_text(first(record, "agent", "AGENT_NAME", "allergen", "name"))
            reaction = clean_text(
                first(record, "reakciya", "react", "reaction", "response")
            )
            value = f"{agent} ({reaction})" if agent and reaction else agent or reaction
        elif isinstance(record, str):
            value = clean_text(record)
        else:
            value = ""
        if value:
            allergies.append(value)
    return deduplicate(allergies)


def _extract_chronic_diseases(source: Any) -> list[str]:
    diseases: list[str] = []
    for record in items(source):
        if isinstance(record, Mapping):
            value = clean_text(
                first(
                    record,
                    "DIAGNOZ_NAME",
                    "diagnoz_name",
                    "diagnosis",
                    "name",
                    "MKB10_KOD",
                    "code",
                )
            )
        elif isinstance(record, str):
            value = clean_text(record)
        else:
            value = ""
        if value:
            diseases.append(value)
    return deduplicate(diseases)


def format_therapy(source: Any) -> list[str]:
    therapy: list[str] = []
    for record in items(source):
        if isinstance(record, Mapping):
            parts = (
                clean_text(first(record, "preparat", "drug", "medication", "name")),
                clean_text(first(record, "doza", "dose")),
                clean_text(first(record, "krat", "frequency", "schedule")),
            )
            value = " ".join(part for part in parts if part)
        elif isinstance(record, str):
            value = clean_text(record)
        else:
            value = ""
        if value:
            therapy.append(value)
    return deduplicate(therapy)


def _latest_therapy(visits: list[Mapping[str, Any]]) -> list[str]:
    latest_key: tuple[bool, str, int] | None = None
    latest_therapy: list[str] = []
    for index, visit in enumerate(visits):
        therapy = format_therapy(
            first(visit, "terapiya", "therapy", "medications", "current_therapy")
        )
        if not therapy:
            continue
        visit_date = normalize_date(
            first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
        )
        candidate_key = (visit_date is not None, visit_date or "", index)
        if latest_key is None or candidate_key > latest_key:
            latest_key = candidate_key
            latest_therapy = therapy
    return latest_therapy


def _latest_visit_measurement(
    visits: list[Mapping[str, Any]], *keys: str
) -> float | None:
    candidates: list[tuple[tuple[bool, str, int], float]] = []
    for index, visit in enumerate(visits):
        measurements = as_mapping(first(visit, "izmereniya", "measurements", "vitals"))
        value = parse_number(first(measurements, *keys))
        if value is None:
            continue
        visit_date = normalize_date(
            first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
        )
        candidates.append(((visit_date is not None, visit_date or "", index), value))
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate[0])[1]
