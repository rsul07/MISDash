"""Shared, parser-independent helpers for quality invariants."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from src.contracts.patient.v1 import PatientRecord
from src.contracts.patient.v1.common import SourceReference


IGNORED_SOURCE_BLOCKS = (
    "EHR_EVENT_LOG",
    "legacy_import_v3",
    "sluzhebnoe",
)
MISSING_STRINGS = {
    "",
    "-",
    "—",
    "n/a",
    "na",
    "nan",
    "none",
    "null",
    "не указано",
    "нет данных",
    "н/д",
}
_ID_FIELDS = {
    "id",
    "pat_id",
    "patient_id",
    "id_priema",
    "visit_id",
    "appointment_id",
    "nomer_zakaza",
    "order_id",
    "report_id",
    "id_pokazatelya",
    "result_id",
    "protokol_id",
    "procedure_id",
    "admission_id",
    "allergy_id",
    "condition_id",
    "medication_id",
    "prescription_id",
    "family_history_id",
}


def medical_data(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    nested = payload.get("data")
    return nested if isinstance(nested, Mapping) else payload


def mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return clean_scalar(value).casefold() in {
        "1",
        "true",
        "yes",
        "да",
    }


def clean_scalar(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        cleaned = " ".join(value.replace("\u00a0", " ").split())
        return "" if cleaned.casefold() in MISSING_STRINGS else cleaned
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().casefold() not in MISSING_STRINGS
    if isinstance(value, float):
        return math.isfinite(value)
    return not isinstance(value, bool)


def parse_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if not isinstance(value, str):
        return None
    normalized = (
        value.strip()
        .replace("\u00a0", "")
        .replace(" ", "")
        .replace(",", ".")
    )
    if normalized.casefold() in MISSING_STRINGS:
        return None
    if not re.fullmatch(
        r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",
        normalized,
    ):
        return None
    try:
        number = float(normalized)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def valid_number(
    value: Any,
    minimum: float,
    maximum: float,
) -> float | None:
    number = parse_number(value)
    if number is None or not minimum <= number <= maximum:
        return None
    return number


def valid_bp(systolic: Any, diastolic: Any) -> bool:
    normalized_systolic = valid_number(systolic, 60, 300)
    normalized_diastolic = valid_number(diastolic, 30, 200)
    return bool(
        normalized_systolic is not None
        and normalized_diastolic is not None
        and normalized_systolic > normalized_diastolic
    )


def source_references(
    record: PatientRecord,
) -> Iterable[tuple[str, SourceReference]]:
    yield "patient", record.patient.source
    if record.social_history is not None:
        yield "social_history", record.social_history.source
    fields = (
        "family_history",
        "allergies",
        "conditions",
        "medications",
        "encounters",
        "observations",
        "procedures",
        "hospitalizations",
        "immunizations",
        "diagnostic_reports",
    )
    for field in fields:
        for index, item in enumerate(getattr(record, field)):
            yield f"{field}[{index}]", item.source


def resolve_path(
    root: Mapping[str, Any],
    path: str,
) -> tuple[Any, tuple[Any, ...]] | str:
    current: Any = root
    ancestors: list[Any] = [root]
    for segment in path.split("."):
        match = re.fullmatch(r"([^\[\]]+)((?:\[\d+\])*)", segment)
        if match is None:
            return f"invalid path syntax: {path!r}"
        key, indexes = match.groups()
        if not isinstance(current, Mapping) or key not in current:
            return f"missing key {key!r} in path {path!r}"
        current = current[key]
        ancestors.append(current)
        for raw_index in re.findall(r"\[(\d+)\]", indexes):
            index = int(raw_index)
            if (
                not isinstance(current, Sequence)
                or isinstance(current, (str, bytes, bytearray))
                or index >= len(current)
            ):
                return f"invalid index {index} in path {path!r}"
            current = current[index]
            ancestors.append(current)
    return current, tuple(ancestors)


def source_id_candidates(value: Any) -> set[str]:
    if not isinstance(value, Mapping):
        return set()
    result: set[str] = set()
    for key, candidate in value.items():
        if not isinstance(key, str):
            continue
        folded = key.casefold()
        if folded not in _ID_FIELDS and not folded.endswith("_id"):
            continue
        normalized = clean_scalar(candidate)
        if normalized:
            result.add(normalized.casefold())
    return result


def top_level_block(block: str) -> str:
    return re.split(r"[.\[]", block, maxsplit=1)[0]

