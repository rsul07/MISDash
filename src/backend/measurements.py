"""Shared classification and unit normalization for clinical measurements."""

from __future__ import annotations

from dataclasses import dataclass

from src.contracts.patient.v1.common import Coding


@dataclass(frozen=True)
class MetricDefinition:
    code: str
    display: str
    unit: str


DIRECT_METRICS = (
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
    MetricDefinition(
        "urine-albumin-creatinine-ratio",
        "Альбумин/креатинин мочи",
        "mg/mmol",
    ),
)
DIRECT_DEFINITIONS = {item.code: item for item in DIRECT_METRICS}


def metric_code(coding: Coding) -> str | None:
    """Map canonical coding/display aliases to a stable dashboard code."""

    code = (coding.code or "").casefold()
    if code in DIRECT_DEFINITIONS:
        return code
    display = coding.display.casefold().replace("ё", "е").strip()
    if "альбумин/креатинин" in display and "моч" in display:
        return "urine-albumin-creatinine-ratio"
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


def normalize_unit(unit: str | None) -> str | None:
    """Normalize units used by direct and calculated metric projections."""

    if unit is None:
        return None
    normalized = unit.casefold().replace(" ", "").replace("μ", "µ")
    aliases = {
        "ммоль/л": "mmol/L",
        "mmol/l": "mmol/L",
        "мкмоль/л": "µmol/L",
        "µmol/l": "µmol/L",
        "umol/l": "µmol/L",
        "мг/дл": "mg/dL",
        "mg/dl": "mg/dL",
        "мг/ммоль": "mg/mmol",
        "mg/mmol": "mg/mmol",
        "ммрт.ст.": "mmHg",
        "ммртст": "mmHg",
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
