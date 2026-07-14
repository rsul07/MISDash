"""Patient header contracts for DashboardResponse v1."""

from __future__ import annotations

from datetime import date

from src.contracts.v1.common import ContractModel


class DashboardPatient(ContractModel):
    id: str
    full_name: str
    birth_date: date | None = None
    age: int | None = None
    gender: str | None = None
    blood_group: str | None = None
    height_cm: float | None = None
    last_weight_kg: float | None = None
    bmi: float | None = None


class AllergySummary(ContractModel):
    agent: str
    reaction: str | None = None


class ConditionSummary(ContractModel):
    code: str | None = None
    display: str
    stage: str | None = None
    clinical_status: str | None = None


class MedicationSummary(ContractModel):
    name: str
    dose: str | None = None
    frequency: str | None = None
    form: str | None = None
