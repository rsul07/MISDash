"""Common value objects used by PatientRecord v1."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


ClinicalDate = date | datetime


class ContractModel(BaseModel):
    """Strict base model for versioned backend contracts."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class SourceReference(ContractModel):
    block: str
    source_id: str | None = None
    path: str | None = None


class Coding(ContractModel):
    code: str | None = None
    display: str
    system: str | None = None


class ReferenceRange(ContractModel):
    low: float | None = None
    high: float | None = None
    text: str | None = None


class Quantity(ContractModel):
    value: float | str | None = None
    unit: str | None = None


class ClinicalEvent(ContractModel):
    id: str
    source: SourceReference
