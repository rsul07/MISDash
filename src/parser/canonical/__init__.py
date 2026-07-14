"""Adapters from dirty MIS blocks to the canonical backend contract."""

from .encounters import EncounterBundle, build_encounters
from .builder import build_patient_record
from .history import HistoryBundle, build_history
from .observations import ObservationBundle, build_observations
from .patient import PatientBundle, build_patient

__all__ = [
    "EncounterBundle",
    "HistoryBundle",
    "ObservationBundle",
    "PatientBundle",
    "build_encounters",
    "build_history",
    "build_observations",
    "build_patient",
    "build_patient_record",
]
