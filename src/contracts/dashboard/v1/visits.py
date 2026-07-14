"""Encounter timeline contracts for DashboardResponse v1."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from src.contracts.patient.v1.common import ContractModel

from .common import CodeLabel


class VisitSummary(ContractModel):
    id: str
    occurred_at: date | datetime | None = None
    practitioner: str | None = None
    specialty: str | None = None
    encounter_type: str | None = None
    diagnoses: list[CodeLabel] = Field(default_factory=list)
    complaints: str | None = None
