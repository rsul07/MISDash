"""Procedure, hospitalization, immunization and report contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import ClinicalDate, ClinicalEvent, Coding


class Procedure(ClinicalEvent):
    coding: Coding
    performed_at: ClinicalDate | None = None
    facility: str | None = None
    outcome: str | None = None
    note: str | None = None


class Hospitalization(ClinicalEvent):
    facility: str | None = None
    admitted_at: ClinicalDate | None = None
    discharged_at: ClinicalDate | None = None
    diagnosis: Coding | None = None
    outcome: str | None = None


class Immunization(ClinicalEvent):
    vaccine: str
    administered_at: ClinicalDate | None = None
    lot_number: str | None = None


class DiagnosticReport(ClinicalEvent):
    category: Literal["laboratory", "instrumental"]
    coding: Coding
    effective_at: ClinicalDate | None = None
    issued_at: ClinicalDate | None = None
    conclusion: str | None = None
    performer: str | None = None
    observation_ids: list[str] = Field(default_factory=list)
    status: str | None = None
