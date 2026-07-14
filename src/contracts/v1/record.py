"""Root PatientRecord v1 contract."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .common import ContractModel
from .encounters import Encounter
from .history import DiagnosticReport, Hospitalization, Immunization, Procedure
from .observations import Observation
from .patient import Allergy, Condition, Medication, Patient


class PatientRecord(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    patient: Patient
    allergies: list[Allergy] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    encounters: list[Encounter] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)
    procedures: list[Procedure] = Field(default_factory=list)
    hospitalizations: list[Hospitalization] = Field(default_factory=list)
    immunizations: list[Immunization] = Field(default_factory=list)
    diagnostic_reports: list[DiagnosticReport] = Field(default_factory=list)
