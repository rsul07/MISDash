"""Generic chart-series contracts for DashboardResponse v1."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from src.contracts.patient.v1.common import ContractModel


class CalculationInfo(ContractModel):
    """Backend-provided explanation for a derived metric series."""

    code: str
    description: str
    inputs: list[str] = Field(default_factory=list)
    purpose: str
    method: str
    standard: str
    limitations: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class CalculationInput(ContractModel):
    """One backend-provided operand of a calculated metric point."""

    display: str
    value: float | int | str
    unit: str | None = None
    source_id: str | None = None


class MetricPoint(ContractModel):
    observed_at: date | datetime
    value: float
    source_category: str
    encounter_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    calculation_inputs: list[CalculationInput] = Field(default_factory=list)
    interpretation: str | None = None


class MetricSeries(ContractModel):
    code: str
    display: str
    unit: str | None = None
    points: list[MetricPoint] = Field(default_factory=list)
    calculation: CalculationInfo | None = None
