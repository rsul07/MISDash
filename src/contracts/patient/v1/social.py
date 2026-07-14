"""Social and family history contracts."""

from __future__ import annotations

from .common import ClinicalEvent, ContractModel, SourceReference


class TobaccoUse(ContractModel):
    status: str | None = None
    years: float | None = None
    cigarettes_per_day: float | None = None
    pack_years: float | None = None
    pack_years_text: str | None = None
    quit_attempts: int | None = None
    note: str | None = None


class AlcoholUse(ContractModel):
    status: str | None = None
    frequency: str | None = None
    audit_c_score: float | None = None


class SocialHistory(ContractModel):
    source: SourceReference
    tobacco: TobaccoUse | None = None
    alcohol: AlcoholUse | None = None
    substance_use: str | None = None
    physical_activity: str | None = None
    occupational_hazards: str | None = None


class FamilyHistory(ClinicalEvent):
    relationship: str | None = None
    condition: str
    onset_age: float | None = None
    outcome: str | None = None
