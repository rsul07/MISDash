"""Patient, condition, allergy and medication contracts."""

from __future__ import annotations

from datetime import date

from .common import ClinicalDate, ClinicalEvent, Coding, ContractModel, SourceReference


class Patient(ContractModel):
    id: str
    full_name: str
    birth_date: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    height_cm: float | None = None
    last_weight_kg: float | None = None
    source: SourceReference


class Allergy(ClinicalEvent):
    agent: str
    reaction: str | None = None
    allergy_type: str | None = None
    onset_year: int | None = None
    note: str | None = None


class Condition(ClinicalEvent):
    coding: Coding
    onset: ClinicalDate | None = None
    stage: str | None = None
    clinical_status: str | None = None
    note: str | None = None


class Medication(ClinicalEvent):
    name: str
    dose: str | None = None
    frequency: str | None = None
    form: str | None = None
    status: str | None = None
    encounter_id: str | None = None
