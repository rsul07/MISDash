"""Canonical encounter, diagnosis and medication adapters."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.contracts.v1 import Diagnosis, Encounter, Medication, Practitioner
from src.contracts.v1.common import Coding

from ..normalizers import clean_text
from ..records import as_mapping, first, items, records, unique_visits
from .common import event_id, original_date_text, source_reference
from .dates import parse_clinical_date


@dataclass(frozen=True)
class EncounterBundle:
    encounters: list[Encounter]
    medications: list[Medication]


def build_encounters(data: Mapping[str, Any]) -> EncounterBundle:
    source = first(
        data,
        "PRIEMY_VRACHA",
        "priemy_vracha",
        "visits",
        "appointments",
    )
    encounters: list[Encounter] = []
    medications: list[Medication] = []
    for index, visit in enumerate(unique_visits(source)):
        source_id = first(visit, "id_priema", "visit_id", "appointment_id", "id")
        encounter_id = canonical_encounter_id(index, source_id)
        visit_medications = _build_medications(visit, index, encounter_id)
        medications.extend(visit_medications)
        follow_up_raw = first(visit, "sled_yavka", "follow_up_at", "next_visit")
        follow_up_at = parse_clinical_date(follow_up_raw)
        doctor = as_mapping(first(visit, "VRACH", "vrach", "doctor", "physician"))
        encounters.append(
            Encounter(
                id=encounter_id,
                source=source_reference("PRIEMY_VRACHA", index, source_id),
                occurred_at=parse_clinical_date(
                    first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
                ),
                practitioner=Practitioner(
                    name=clean_text(first(doctor, "fio_doc", "FIO", "fio", "name"))
                    or None,
                    specialty=clean_text(
                        first(doctor, "spec_name", "specialty", "speciality")
                    )
                    or None,
                ),
                encounter_type=clean_text(
                    first(visit, "vid_priema", "encounter_type", "visit_type")
                )
                or None,
                location=clean_text(first(doctor, "kabinet", "location", "room"))
                or None,
                complaints=clean_text(
                    first(visit, "JALOBY_TXT", "jaloby_txt", "complaints")
                )
                or None,
                history=clean_text(first(visit, "anamnez_txt", "history", "anamnesis"))
                or None,
                objective=clean_text(
                    first(visit, "obektivny_status", "objective_status", "objective")
                )
                or None,
                diagnoses=_build_diagnoses(visit),
                plan=clean_text(
                    first(visit, "naznacheniya_txt", "plan", "recommendations")
                )
                or None,
                follow_up_at=follow_up_at,
                follow_up_at_text=original_date_text(follow_up_raw, follow_up_at),
                medication_ids=[medication.id for medication in visit_medications],
                status=clean_text(first(visit, "status_zapisi", "status")) or None,
            )
        )
    return EncounterBundle(encounters=encounters, medications=medications)


def canonical_encounter_id(index: int, source_id: Any) -> str:
    normalized = clean_text(source_id)
    if normalized:
        normalized = re.sub(
            r"[_-]dup(?:licate)?$", "", normalized, flags=re.IGNORECASE
        )
    return normalized or event_id("encounter", index)


def _build_diagnoses(visit: Mapping[str, Any]) -> list[Diagnosis]:
    source = first(
        visit,
        "diagnoz_priema",
        "diagnosis",
        "diagnoz",
        "visit_diagnosis",
    )
    diagnosis = as_mapping(source)
    primary_code = clean_text(
        first(diagnosis, "osnovnoy_MKB", "code", "icd10")
    )
    primary_display = clean_text(
        first(diagnosis, "osnovnoy_txt", "diagnosis", "name")
    )
    if not primary_display and not diagnosis:
        primary_display = clean_text(source)

    result: list[Diagnosis] = []
    if primary_display or primary_code:
        result.append(
            Diagnosis(
                coding=Coding(
                    code=primary_code or None,
                    display=primary_display or primary_code,
                    system="ICD-10" if primary_code else None,
                ),
                role="primary",
            )
        )
    for item in items(first(diagnosis, "soputstv", "secondary", "comorbidities")):
        coding = _secondary_coding(item)
        if coding is not None:
            result.append(Diagnosis(coding=coding, role="secondary"))
    return result


def _secondary_coding(value: Any) -> Coding | None:
    if isinstance(value, Mapping):
        code = clean_text(first(value, "code", "MKB10", "icd10"))
        display = clean_text(first(value, "display", "diagnosis", "name"))
    else:
        text = clean_text(value)
        match = re.match(r"^(?P<code>[A-ZА-Я]\d{2}(?:\.\d+)?)\s+(?P<display>.+)$", text)
        code = match.group("code") if match else ""
        display = match.group("display") if match else text
    if not code and not display:
        return None
    return Coding(
        code=code or None,
        display=display or code,
        system="ICD-10" if code else None,
    )


def _build_medications(
    visit: Mapping[str, Any],
    visit_index: int,
    encounter_id: str,
) -> list[Medication]:
    source = first(visit, "terapiya", "therapy", "medications", "current_therapy")
    result: list[Medication] = []
    for index, item in enumerate(items(source)):
        mapping = as_mapping(item)
        name = clean_text(
            first(mapping, "preparat", "drug", "medication", "name")
        )
        if not name:
            name = clean_text(item)
        if not name:
            continue
        source_id = first(mapping, "id", "medication_id", "prescription_id")
        result.append(
            Medication(
                id=event_id(f"{encounter_id}-medication", index, source_id),
                source=source_reference(
                    f"PRIEMY_VRACHA[{visit_index}].terapiya", index, source_id
                ),
                name=name,
                dose=clean_text(first(mapping, "doza", "dose")) or None,
                frequency=clean_text(first(mapping, "krat", "frequency", "schedule"))
                or None,
                form=clean_text(first(mapping, "forma", "form")) or None,
                status=clean_text(first(mapping, "status")) or None,
                encounter_id=encounter_id,
            )
        )
    return result
