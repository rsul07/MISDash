"""KDIGO measurement categories without inferring a CKD diagnosis."""

from __future__ import annotations

from .validation import non_negative_number


def classify_egfr_category(egfr: float) -> str:
    """Return the KDIGO G category for an eGFR value."""

    value = non_negative_number(egfr, name="egfr")
    if value >= 90:
        return "G1"
    if value >= 60:
        return "G2"
    if value >= 45:
        return "G3a"
    if value >= 30:
        return "G3b"
    if value >= 15:
        return "G4"
    return "G5"


def classify_albuminuria_category(acr_mg_mmol: float) -> str:
    """Return the KDIGO A category for urine ACR in mg/mmol."""

    value = non_negative_number(acr_mg_mmol, name="acr_mg_mmol")
    if value < 3:
        return "A1"
    if value <= 30:
        return "A2"
    return "A3"
