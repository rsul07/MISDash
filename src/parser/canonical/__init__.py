"""Adapters from dirty MIS blocks to the canonical backend contract."""

from .encounters import EncounterBundle, build_encounters
from .history import HistoryBundle, build_history
from .patient import PatientBundle, build_patient

__all__ = [
    "EncounterBundle",
    "HistoryBundle",
    "PatientBundle",
    "build_encounters",
    "build_history",
    "build_patient",
]
