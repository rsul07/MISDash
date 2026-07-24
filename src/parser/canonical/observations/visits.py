"""Vital-sign observations recorded during encounters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.contracts.patient.v1 import Observation

from ...extractors import extract_vitals_from_text
from ...normalizers import valid_bp_pair, valid_number
from ...records import as_mapping, first, indexed_unique_visits
from ..common import source_reference
from ..dates import parse_clinical_date
from ..encounters import canonical_encounter_id
from .common import blood_pressure_observation, coding, quantity


_MEASUREMENTS = (
    ("heart-rate", "Частота сердечных сокращений", "beats/min", ("CHSS", "heart_rate", "pulse"), 20, 250),
    ("body-weight", "Масса тела", "kg", ("ves", "weight", "weight_kg"), 1, 500),
    ("body-height", "Рост", "cm", ("rost", "height", "height_cm"), 30, 250),
    ("bmi", "Индекс массы тела", "kg/m2", ("IMT_calc", "bmi", "IMT"), 5, 100),
    ("waist-circumference", "Окружность талии", "cm", ("okrujnost_talii_sm", "waist_cm"), 20, 300),
    ("oxygen-saturation", "Сатурация кислорода", "%", ("SpO2", "spo2"), 30, 100),
    ("body-temperature", "Температура тела", "Cel", ("temperatura", "temperature"), 25, 45),
)


def build_visit_observations(data: Mapping[str, Any]) -> list[Observation]:
    source = first(
        data,
        "PRIEMY_VRACHA",
        "priemy_vracha",
        "visits",
        "appointments",
    )
    result: list[Observation] = []
    for index, (source_index, visit) in enumerate(indexed_unique_visits(source)):
        source_id = first(visit, "id_priema", "visit_id", "appointment_id", "id")
        encounter_id = canonical_encounter_id(index, source_id)
        observed_at = parse_clinical_date(
            first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
        )
        measurements = as_mapping(
            first(visit, "izmereniya", "measurements", "vitals")
        )
        source_ref = source_reference(
            f"PRIEMY_VRACHA[{source_index}].izmereniya", source_id=source_id
        )
        bp_pair, bp_method = _blood_pressure(visit, measurements)
        if bp_pair is not None:
            result.append(
                blood_pressure_observation(
                    observation_id=f"{encounter_id}-blood-pressure",
                    source=source_ref,
                    observed_at=observed_at,
                    category="vital-signs",
                    systolic=bp_pair[0],
                    diastolic=bp_pair[1],
                    encounter_id=encounter_id,
                    method=bp_method,
                )
            )
        result.extend(
            _scalar_measurements(
                visit,
                measurements,
                index,
                encounter_id,
                observed_at,
                source_ref,
            )
        )
    return result


def _blood_pressure(
    visit: Mapping[str, Any], measurements: Mapping[str, Any]
) -> tuple[tuple[float, float] | None, str | None]:
    structured = valid_bp_pair(
        first(measurements, "AD_sist", "sys_bp", "sys", "systolic"),
        first(measurements, "AD_diast", "dia_bp", "dia", "diastolic"),
    )
    if structured is not None:
        return structured, "structured"
    for field in (
        ("obektivny_status", "objective_status", "objective"),
        ("JALOBY_TXT", "jaloby_txt", "complaints"),
    ):
        extracted = extract_vitals_from_text(first(visit, *field))
        pair = valid_bp_pair(extracted["sys_bp"], extracted["dia_bp"])
        if pair is not None:
            return pair, "text-extraction"
    return None, None


def _scalar_measurements(
    visit: Mapping[str, Any],
    measurements: Mapping[str, Any],
    visit_index: int,
    encounter_id: str,
    observed_at: Any,
    source_ref: Any,
) -> list[Observation]:
    result: list[Observation] = []
    for code, display, unit, aliases, minimum, maximum in _MEASUREMENTS:
        value = valid_number(first(measurements, *aliases), minimum, maximum)
        method = "structured"
        if code == "heart-rate" and value is None:
            value = _heart_rate_from_text(visit)
            method = "text-extraction"
        if value is None:
            continue
        result.append(
            Observation(
                id=f"{encounter_id}-{code}",
                source=source_ref,
                observed_at=observed_at,
                category="vital-signs",
                coding=coding(display, code),
                value=quantity(value, unit),
                method=method,
                encounter_id=encounter_id,
            )
        )
    return result


def _heart_rate_from_text(visit: Mapping[str, Any]) -> float | None:
    for field in (
        ("obektivny_status", "objective_status", "objective"),
        ("JALOBY_TXT", "jaloby_txt", "complaints"),
    ):
        extracted = extract_vitals_from_text(first(visit, *field))
        value = valid_number(extracted["heart_rate"], 20, 250)
        if value is not None:
            return value
    return None
