"""Bind canonical patient observations to pure clinical calculators."""

from src.calculators import CalculatedValue
from src.contracts.patient.v1 import PatientRecord

from .blood_pressure import calculate_pulse_pressure_metrics
from .kidney import calculate_egfr_metrics
from .lipids import calculate_lipid_metrics


def calculate_record_metrics(record: PatientRecord) -> list[CalculatedValue]:
    """Calculate every safe derived metric supported by a patient record."""

    return [
        *calculate_egfr_metrics(record),
        *calculate_lipid_metrics(record),
        *calculate_pulse_pressure_metrics(record),
    ]


__all__ = ["calculate_record_metrics"]
