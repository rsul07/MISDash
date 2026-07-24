"""Composition of independent generated-value fidelity checks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.contracts.patient.v1 import PatientRecord

from .dates import date_fidelity_check
from .models import QualityCheck
from .numeric import numeric_fidelity_check


def fidelity_checks(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> tuple[QualityCheck, QualityCheck]:
    return (
        numeric_fidelity_check(data, record),
        date_fidelity_check(data, record),
    )
