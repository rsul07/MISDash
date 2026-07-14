"""Generic chart-series contracts for DashboardResponse v1."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from src.contracts.v1.common import ContractModel


class MetricPoint(ContractModel):
    observed_at: date | datetime
    value: float
    source_category: str
    encounter_id: str | None = None


class MetricSeries(ContractModel):
    code: str
    display: str
    unit: str | None = None
    points: list[MetricPoint] = Field(default_factory=list)
