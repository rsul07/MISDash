"""Self-monitoring diary observation adapter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.contracts.patient.v1 import Observation

from ...normalizers import clean_text, valid_bp_pair, valid_number
from ...records import as_mapping, first, records
from ..common import source_reference
from ..dates import parse_clinical_date
from .common import blood_pressure_observation, coding, quantity, text_context


def build_diary_observations(data: Mapping[str, Any]) -> list[Observation]:
    diary = as_mapping(
        first(data, "dnevnik_samokontrolya", "self_monitoring_diary", "self_monitoring")
    )
    result: list[Observation] = []
    result.extend(
        _blood_pressure(first(diary, "AD_izmereniya", "blood_pressure", "bp"))
    )
    result.extend(_glucose(first(diary, "glikemiya", "glycemia", "glucose")))
    return result


def _blood_pressure(source: Any) -> list[Observation]:
    result: list[Observation] = []
    for index, item in enumerate(records(source)):
        observed_at = parse_clinical_date(
            first(item, "dt", "date", "measured_at", "izmereno")
        )
        source_ref = source_reference(
            "dnevnik_samokontrolya.AD_izmereniya", index
        )
        pair = valid_bp_pair(
            first(item, "sys", "sys_bp", "systolic"),
            first(item, "dia", "dia_bp", "diastolic"),
        )
        device = clean_text(first(item, "device_id", "device")) or None
        context = text_context(
            period=first(item, "period_dnya", "period"),
            input_source=first(item, "istochnik", "source"),
        )
        if pair is not None:
            result.append(
                blood_pressure_observation(
                    observation_id=f"diary-blood-pressure-{index + 1}",
                    source=source_ref,
                    observed_at=observed_at,
                    category="self-monitoring",
                    systolic=pair[0],
                    diastolic=pair[1],
                    device=device,
                    context=context,
                )
            )
        pulse = valid_number(first(item, "pulse", "heart_rate", "CHSS"), 20, 250)
        if pulse is not None:
            result.append(
                Observation(
                    id=f"diary-heart-rate-{index + 1}",
                    source=source_ref,
                    observed_at=observed_at,
                    category="self-monitoring",
                    coding=coding("Частота сердечных сокращений", "heart-rate"),
                    value=quantity(pulse, "beats/min"),
                    device=device,
                    context=context,
                )
            )
    return result


def _glucose(source: Any) -> list[Observation]:
    result: list[Observation] = []
    for index, item in enumerate(records(source)):
        value = first(item, "glukoza_mmol", "glucose", "value", "REZULT")
        normalized = quantity(value, "mmol/L")
        if normalized.value is None:
            continue
        result.append(
            Observation(
                id=f"diary-glucose-{index + 1}",
                source=source_reference("dnevnik_samokontrolya.glikemiya", index),
                observed_at=parse_clinical_date(
                    first(item, "izmereno", "dt", "date", "measured_at")
                ),
                category="self-monitoring",
                coding=coding("Глюкоза крови", "glucose"),
                value=normalized,
                device=clean_text(first(item, "glukometr", "device")) or None,
                context=text_context(
                    measurement_condition=first(item, "usloviya", "condition")
                ),
            )
        )
    return result
