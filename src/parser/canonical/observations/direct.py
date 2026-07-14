"""Adapter for already structured generic vital-sign records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.contracts.patient.v1 import Observation

from ...normalizers import valid_bp_pair
from ...records import first, records
from ..common import source_reference
from ..dates import parse_clinical_date
from .common import blood_pressure_observation, coding, quantity


_FIELDS = (
    ("heart-rate", "Частота сердечных сокращений", "beats/min", ("heart_rate", "pulse", "CHSS")),
    ("body-weight", "Масса тела", "kg", ("weight", "weight_kg", "ves")),
    ("glucose", "Глюкоза крови", "mmol/L", ("glucose", "glukoza_mmol")),
    ("hba1c", "Гликированный гемоглобин", "%", ("hba1c", "HbA1c")),
    ("creatinine", "Креатинин", None, ("creatinine", "kreatinin")),
    ("total-cholesterol", "Общий холестерин", None, ("cholesterol", "total_cholesterol")),
)


def build_direct_observations(data: Mapping[str, Any]) -> list[Observation]:
    source = first(data, "vitals", "vital_signs", "measurements")
    result: list[Observation] = []
    for index, item in enumerate(records(source)):
        observed_at = parse_clinical_date(
            first(item, "date", "dt", "measured_at", "izmereno")
        )
        pair = valid_bp_pair(
            first(item, "sys_bp", "sys", "systolic", "AD_sist"),
            first(item, "dia_bp", "dia", "diastolic", "AD_diast"),
        )
        source_ref = source_reference("vitals", index, first(item, "id"))
        if pair is not None:
            result.append(
                blood_pressure_observation(
                    observation_id=f"direct-{index + 1}-blood-pressure",
                    source=source_ref,
                    observed_at=observed_at,
                    category="vital-signs",
                    systolic=pair[0],
                    diastolic=pair[1],
                )
            )
        for code, display, unit, aliases in _FIELDS:
            value = first(item, *aliases)
            normalized = quantity(value, unit)
            if normalized.value is None:
                continue
            result.append(
                Observation(
                    id=f"direct-{index + 1}-{code}",
                    source=source_ref,
                    observed_at=observed_at,
                    category="vital-signs",
                    coding=coding(display, code),
                    value=normalized,
                )
            )
    return result
