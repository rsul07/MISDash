"""Composition root for the canonical PatientRecord contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.contracts.v1 import PatientRecord

from .encounters import build_encounters
from .history import build_history
from .observations import build_observations
from .patient import build_patient
from .social import build_social_history


def build_patient_record(data: Mapping[str, Any]) -> PatientRecord:
    patient = build_patient(data)
    encounters = build_encounters(data)
    observations = build_observations(data)
    history = build_history(data)
    social = build_social_history(data)
    return PatientRecord(
        patient=patient.patient,
        social_history=social.social_history,
        family_history=social.family_history,
        allergies=patient.allergies,
        conditions=patient.conditions,
        medications=encounters.medications,
        encounters=encounters.encounters,
        observations=observations.observations,
        procedures=history.procedures,
        hospitalizations=history.hospitalizations,
        immunizations=history.immunizations,
        diagnostic_reports=[
            *observations.diagnostic_reports,
            *history.diagnostic_reports,
        ],
    )
