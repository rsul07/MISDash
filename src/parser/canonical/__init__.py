"""Adapters from dirty MIS blocks to the canonical backend contract."""

from .history import HistoryBundle, build_history
from .patient import PatientBundle, build_patient

__all__ = ["HistoryBundle", "PatientBundle", "build_history", "build_patient"]
