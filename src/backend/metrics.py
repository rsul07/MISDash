"""Stable chart-series projection from canonical observations."""

from __future__ import annotations

from dataclasses import dataclass

from src.contracts.dashboard.v1 import MetricPoint, MetricSeries
from src.contracts.patient.v1 import Observation, PatientRecord
from src.contracts.patient.v1.common import Coding, Quantity

from .common import chronological_key


@dataclass(frozen=True)
class MetricDefinition:
    code: str
    display: str
    unit: str


METRICS = (
    MetricDefinition("systolic", "Систолическое АД", "mmHg"),
    MetricDefinition("diastolic", "Диастолическое АД", "mmHg"),
    MetricDefinition("heart-rate", "Частота сердечных сокращений", "beats/min"),
    MetricDefinition("body-weight", "Масса тела", "kg"),
    MetricDefinition("bmi", "Индекс массы тела", "kg/m2"),
    MetricDefinition("glucose", "Глюкоза крови", "mmol/L"),
    MetricDefinition("hba1c", "Гликированный гемоглобин", "%"),
    MetricDefinition("creatinine", "Креатинин", "µmol/L"),
    MetricDefinition("total-cholesterol", "Общий холестерин", "mmol/L"),
    MetricDefinition("ldl-cholesterol", "Холестерин ЛПНП", "mmol/L"),
    MetricDefinition("hdl-cholesterol", "Холестерин ЛПВП", "mmol/L"),
    MetricDefinition("triglycerides", "Триглицериды", "mmol/L"),
    MetricDefinition("potassium", "Калий", "mmol/L"),
    MetricDefinition("oxygen-saturation", "Сатурация кислорода", "%"),
    MetricDefinition("body-temperature", "Температура тела", "Cel"),
)
_DEFINITIONS = {item.code: item for item in METRICS}


def build_metric_series(record: PatientRecord) -> list[MetricSeries]:
    points: dict[str, list[MetricPoint]] = {
        definition.code: [] for definition in METRICS
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
    for definition in METRICS:
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
    metric_code = _metric_code(coding)
    if metric_code is None:
        return
    definition = _DEFINITIONS[metric_code]
    unit = _normalize_unit(quantity.unit)
    if unit is not None and unit != definition.unit:
        return
    points[metric_code].append(
        MetricPoint(
            observed_at=observation.observed_at,
            value=float(quantity.value),
            source_category=observation.category,
            encounter_id=observation.encounter_id,
        )
    )


def _metric_code(coding: Coding) -> str | None:
    code = (coding.code or "").casefold()
    if code in _DEFINITIONS:
        return code
    display = coding.display.casefold().replace("ё", "е").strip()
    if "глюкоз" in display and "моч" not in display:
        return "glucose"
    if "hba1c" in display or "гликирован" in display:
        return "hba1c"
    if "креатинин" in display and "моч" not in display and "альбумин" not in display:
        return "creatinine"
    if display in {"холестерин общий", "общий холестерин", "total cholesterol"}:
        return "total-cholesterol"
    if "лпнп" in display or "ldl" in display:
        return "ldl-cholesterol"
    if "лпвп" in display or "hdl" in display:
        return "hdl-cholesterol"
    if "триглицерид" in display:
        return "triglycerides"
    if display in {"калий", "potassium"}:
        return "potassium"
    return None


def _normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    normalized = unit.casefold().replace(" ", "").replace("μ", "µ")
    aliases = {
        "ммоль/л": "mmol/L",
        "mmol/l": "mmol/L",
        "мкмоль/л": "µmol/L",
        "µmol/l": "µmol/L",
        "ммрт.ст.": "mmHg",
        "mmhg": "mmHg",
        "уд/мин": "beats/min",
        "beats/min": "beats/min",
        "кг": "kg",
        "kg": "kg",
        "кг/м2": "kg/m2",
        "kg/m2": "kg/m2",
        "%": "%",
        "cel": "Cel",
        "°c": "Cel",
    }
    return aliases.get(normalized, unit)
