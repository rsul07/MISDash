"""Encounter and diagnosis contracts."""

from __future__ import annotations

from pydantic import Field

from .common import ClinicalDate, ClinicalEvent, Coding, ContractModel


class Practitioner(ContractModel):
    name: str | None = None
    specialty: str | None = None


class Diagnosis(ContractModel):
    coding: Coding
    role: str = "primary"


class Encounter(ClinicalEvent):
    occurred_at: ClinicalDate | None = None
    practitioner: Practitioner = Field(default_factory=Practitioner)
    encounter_type: str | None = None
    complaints: str | None = None
    history: str | None = None
    objective: str | None = None
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    plan: str | None = None
    medication_ids: list[str] = Field(default_factory=list)
    status: str | None = None
