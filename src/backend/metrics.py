"""Stable chart-series projection from canonical observations."""

from __future__ import annotations

from src.calculators import (
    CalculatedValue,
    CalculatorDefinition,
    classify_albuminuria_category,
)
from src.contracts.dashboard.v1 import CalculationInfo, MetricPoint, MetricSeries
from src.contracts.patient.v1 import Observation, PatientRecord
from src.contracts.patient.v1.common import Coding, Quantity

from .calculations import calculate_record_metrics
from .common import chronological_key
from .measurements import DIRECT_DEFINITIONS, DIRECT_METRICS, metric_code, normalize_unit


def build_metric_series(record: PatientRecord) -> list[MetricSeries]:
    points: dict[str, list[MetricPoint]] = {
        definition.code: [] for definition in DIRECT_METRICS
    }
    for observation in record.observations:
        _collect_scalar(points, observation)
        for component in observation.components:
            _collect_value(
                points,
                observation,
                component.coding,
                component.value,
            )

    result: list[MetricSeries] = []
    for definition in DIRECT_METRICS:
        series_points = points[definition.code]
        if not series_points:
            continue
        series_points.sort(
            key=lambda item: (
                chronological_key(item.observed_at),
                item.source_category,
            )
        )
        result.append(
            MetricSeries(
                code=definition.code,
                display=definition.display,
                unit=definition.unit,
                points=series_points,
            )
        )
    result.extend(_build_calculated_series(record))
    return result


def _collect_scalar(
    points: dict[str, list[MetricPoint]],
    observation: Observation,
) -> None:
    if observation.value is None:
        return
    _collect_value(
        points,
        observation,
        observation.coding,
        observation.value,
    )


def _collect_value(
    points: dict[str, list[MetricPoint]],
    observation: Observation,
    coding: Coding,
    quantity: Quantity,
) -> None:
    if observation.observed_at is None or not isinstance(quantity.value, (int, float)):
        return
    code = metric_code(coding)
    if code is None:
        return
    definition = DIRECT_DEFINITIONS[code]
    unit = normalize_unit(quantity.unit)
    if unit != definition.unit:
        return
    points[code].append(
        MetricPoint(
            observed_at=observation.observed_at,
            value=float(quantity.value),
            source_category=observation.category,
            encounter_id=observation.encounter_id,
            source_ids=[observation.id],
            interpretation=_direct_interpretation(code, float(quantity.value)),
        )
    )


def _build_calculated_series(record: PatientRecord) -> list[MetricSeries]:
    grouped: dict[str, list[CalculatedValue]] = {}
    definitions: dict[str, CalculatorDefinition] = {}
    for item in calculate_record_metrics(record):
        grouped.setdefault(item.definition.code, []).append(item)
        definitions[item.definition.code] = item.definition

    result: list[MetricSeries] = []
    for code, calculated_values in grouped.items():
        values = sorted(
            calculated_values,
            key=lambda item: chronological_key(item.observed_at),
        )
        definition = definitions[code]
        result.append(
            MetricSeries(
                code=definition.code,
                display=definition.display,
                unit=definition.unit,
                points=[
                    MetricPoint(
                        observed_at=item.observed_at,
                        value=item.value,
                        source_category="calculated",
                        source_ids=list(item.source_ids),
                        interpretation=item.interpretation,
                    )
                    for item in values
                ],
                calculation=CalculationInfo(
                    code=definition.code,
                    description=definition.description,
                    inputs=list(definition.inputs),
                    purpose=definition.purpose,
                    method=definition.method,
                    standard=definition.standard,
                    limitations=list(definition.limitations),
                    references=list(definition.references),
                ),
            )
        )
    return result


def _direct_interpretation(code: str, value: float) -> str | None:
    if code != "urine-albumin-creatinine-ratio":
        return None
    try:
        return classify_albuminuria_category(value)
    except ValueError:
        return None
