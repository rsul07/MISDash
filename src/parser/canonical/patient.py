"""Canonical patient, allergy and chronic-condition adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.contracts.v1 import Allergy, Condition, Patient
from src.contracts.v1.common import Coding

from ..normalizers import clean_name, clean_text, normalize_date, parse_number
from ..records import as_mapping, first, records, truthy_flag
from .common import event_id, source_reference
from .dates import parse_clinical_date


@dataclass(frozen=True)
class PatientBundle:
    patient: Patient
    allergies: list[Allergy]
    conditions: list[Condition]


def build_patient(data: Mapping[str, Any]) -> PatientBundle:
    source = as_mapping(first(data, "PATIENT_INFO", "patient_info", "patient"))
    patient_id = clean_text(first(source, "pat_id", "patient_id", "id")) or "patient"
    full_name = _full_name(source)
    birth_date_text = normalize_date(
        first(source, "birht_date", "birtf_date", "birth_date", "DATE_ROJD")
    )
    patient = Patient(
        id=patient_id,
        full_name=full_name,
        birth_date=date.fromisoformat(birth_date_text) if birth_date_text else None,
        gender=_gender_code(first(source, "gender", "sex", "pol", "SEX_ID")),
        blood_group=clean_text(first(source, "blood_grp", "blood_group")) or None,
        height_cm=parse_number(first(source, "rost_sm", "height_cm", "height")),
        last_weight_kg=parse_number(
            first(source, "ves_kg_last", "weight_kg", "weight")
        ),
        source=source_reference("PATIENT_INFO", source_id=patient_id),
    )
    return PatientBundle(
        patient=patient,
        allergies=_build_allergies(data),
        conditions=_build_conditions(data),
    )


def _full_name(patient: Mapping[str, Any]) -> str:
    name = clean_name(first(patient, "FIO", "fio", "full_name", "name"))
    if name:
        return name
    return clean_name(
        " ".join(
            filter(
                None,
                (
                    clean_text(first(patient, "pat_fam", "last_name")),
                    clean_text(first(patient, "pat_im", "first_name")),
                    clean_text(first(patient, "pat_otch", "middle_name")),
                ),
            )
        )
    )


def _gender_code(value: Any) -> str | None:
    normalized = clean_text(value).casefold()
    if normalized in {"м", "муж", "мужской", "male", "m", "1"}:
        return "male"
    if normalized in {"ж", "жен", "женский", "female", "f", "2"}:
        return "female"
    return normalized or None


def _build_allergies(data: Mapping[str, Any]) -> list[Allergy]:
    social = as_mapping(first(data, "social_anamnez", "social_history"))
    source = first(social, "allergoanamnez", "allergies", "allergy_history")
    result: list[Allergy] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(records(source)):
        note = clean_text(first(item, "note", "prim", "comment"))
        if "дубл" in note.casefold() or truthy_flag(first(item, "is_deleted", "deleted")):
            continue
        agent = clean_text(first(item, "agent", "AGENT_NAME", "allergen", "name"))
        reaction = clean_text(first(item, "reakciya", "react", "reaction"))
        identity = (agent.casefold(), reaction.casefold())
        if not agent or identity in seen:
            continue
        seen.add(identity)
        year = parse_number(first(item, "god_vyyavl", "onset_year", "year"))
        result.append(
            Allergy(
                id=event_id("allergy", index, first(item, "id", "allergy_id")),
                source=source_reference("social_anamnez.allergoanamnez", index),
                agent=agent,
                reaction=reaction or None,
                allergy_type=clean_text(first(item, "tip", "type")) or None,
                onset_year=int(year) if year is not None else None,
                note=note or None,
            )
        )
    return result


def _build_conditions(data: Mapping[str, Any]) -> list[Condition]:
    source = first(data, "hron_zabolevaniya", "chronic_conditions", "conditions")
    result: list[Condition] = []
    for index, item in enumerate(records(source)):
        code = clean_text(first(item, "MKB10_KOD", "code", "icd10"))
        display = clean_text(first(item, "DIAGNOZ_NAME", "diagnosis", "name"))
        if not display and not code:
            continue
        result.append(
            Condition(
                id=event_id("condition", index, first(item, "id", "condition_id")),
                source=source_reference("hron_zabolevaniya", index),
                coding=Coding(
                    code=code or None,
                    display=display or code,
                    system="ICD-10" if code else None,
                ),
                onset=parse_clinical_date(
                    first(item, "data_ustanovl", "onset", "diagnosed_at")
                ),
                stage=clean_text(first(item, "stadia", "stage")) or None,
                clinical_status=clean_text(first(item, "status", "clinical_status"))
                or None,
                note=clean_text(first(item, "prim", "note", "comment")) or None,
            )
        )
    return result
