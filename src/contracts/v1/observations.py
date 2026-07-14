"""Vital sign and laboratory observation contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import (
    ClinicalDate,
    ClinicalEvent,
    Coding,
    ContractModel,
    Quantity,
    ReferenceRange,
)


ObservationCategory = Literal[
    "vital-signs",
    "laboratory",
    "self-monitoring",
    "clinical",
]


class ObservationComponent(ContractModel):
    coding: Coding
    value: Quantity
    reference_range: ReferenceRange | None = None
    interpretation: str | None = None


class Observation(ClinicalEvent):
    observed_at: ClinicalDate | None = None
    category: ObservationCategory
    coding: Coding
    value: Quantity | None = None
    components: list[ObservationComponent] = Field(default_factory=list)
    reference_range: ReferenceRange | None = None
    interpretation: str | None = None
    method: str | None = None
    status: str | None = None
    encounter_id: str | None = None
    report_id: str | None = None
