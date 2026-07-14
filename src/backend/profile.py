"""Patient header projection for DashboardResponse v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.contracts.dashboard.v1 import (
    AllergySummary,
    ConditionSummary,
    DashboardPatient,
    MedicationSummary,
)
from src.contracts.v1 import Observation, PatientRecord

from .common import chronological_key


@dataclass(frozen=True)
class ProfileProjection:
    patient: DashboardPatient
    allergies: list[AllergySummary]
    conditions: list[ConditionSummary]
    current_medications: list[MedicationSummary]


def build_profile_projection(
    record: PatientRecord,
    as_of: date,
) -> ProfileProjection:
    weight = _latest_measurement(record, "body-weight")
    height = _latest_measurement(record, "body-height")
    bmi = _latest_measurement(record, "bmi")
    weight = weight if weight is not None else record.patient.last_weight_kg
    height = height if height is not None else record.patient.height_cm
    if bmi is None and weight is not None and height is not None and height > 0:
        bmi = round(weight / ((height / 100) ** 2), 1)

    patient = DashboardPatient(
        id=record.patient.id,
        full_name=record.patient.full_name,
        birth_date=record.patient.birth_date,
        age=_age(record.patient.birth_date, as_of),
        gender=record.patient.gender,
        blood_group=record.patient.blood_group,
        height_cm=height,
        last_weight_kg=weight,
        bmi=bmi,
    )
    return ProfileProjection(
        patient=patient,
        allergies=[
            AllergySummary(agent=item.agent, reaction=item.reaction)
            for item in record.allergies
        ],
        conditions=[
            ConditionSummary(
                code=item.coding.code,
                display=item.coding.display,
                stage=item.stage,
                clinical_status=item.clinical_status,
            )
            for item in record.conditions
        ],
        current_medications=_current_medications(record),
    )


def _latest_measurement(record: PatientRecord, code: str) -> float | None:
    candidates: list[Observation] = []
    for observation in record.observations:
        if observation.coding.code != code or observation.value is None:
            continue
        if isinstance(observation.value.value, (int, float)):
            candidates.append(observation)
    if not candidates:
        return None
    latest = max(candidates, key=lambda item: chronological_key(item.observed_at))
    value = latest.value.value if latest.value is not None else None
    return float(value) if isinstance(value, (int, float)) else None


def _current_medications(record: PatientRecord) -> list[MedicationSummary]:
    medication_by_id = {item.id: item for item in record.medications}
    encounters = [item for item in record.encounters if item.medication_ids]
    if encounters:
        latest = max(
            encounters,
            key=lambda item: chronological_key(item.occurred_at),
        )
        medications = [
            medication_by_id[item_id]
            for item_id in latest.medication_ids
            if item_id in medication_by_id
        ]
    else:
        medications = [
            item for item in record.medications if item.encounter_id is None
        ]
    return [
        MedicationSummary(
            name=item.name,
            dose=item.dose,
            frequency=item.frequency,
            form=item.form,
        )
        for item in medications
    ]


def _age(birth_date: date | None, as_of: date) -> int | None:
    if birth_date is None or birth_date > as_of:
        return None
    return as_of.year - birth_date.year - (
        (as_of.month, as_of.day) < (birth_date.month, birth_date.day)
    )
