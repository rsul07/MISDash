"""Persistence boundaries for versioned application contracts."""

from .patient_records import load_patient_record, save_patient_record

__all__ = ["load_patient_record", "save_patient_record"]
