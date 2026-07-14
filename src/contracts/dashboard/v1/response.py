"""Root DashboardResponse v1 contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from src.contracts.v1.common import ContractModel

from .metrics import MetricSeries
from .profile import (
    AllergySummary,
    ConditionSummary,
    DashboardPatient,
    MedicationSummary,
)
from .visits import VisitSummary


class RedFlag(ContractModel):
    code: str
    severity: Literal["info", "warning", "critical"]
    title: str
    explanation: str


class DashboardResponse(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    patient: DashboardPatient
    allergies: list[AllergySummary] = Field(default_factory=list)
    conditions: list[ConditionSummary] = Field(default_factory=list)
    current_medications: list[MedicationSummary] = Field(default_factory=list)
    metrics: list[MetricSeries] = Field(default_factory=list)
    visits: list[VisitSummary] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)
    ai_summary: str | None = None
