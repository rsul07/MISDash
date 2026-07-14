"""Helpers for tolerant traversal and deduplication of MIS records."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from .constants import RECORD_HINT_KEYS
from .normalizers import clean_text, has_value, normalize_date


def as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def first(mapping: Mapping[str, Any], *keys: str) -> Any:
    if not isinstance(mapping, Mapping):
        return None
    for key in keys:
        value = mapping.get(key)
        if has_value(value):
            return value

    folded = {
        key.casefold(): value
        for key, value in mapping.items()
        if isinstance(key, str)
    }
    for key in keys:
        value = folded.get(key.casefold())
        if has_value(value):
            return value
    return None


def records(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if not value:
            return []
        keys = {key.casefold() for key in value if isinstance(key, str)}
        if keys & RECORD_HINT_KEYS:
            return [value]
        nested = list(value.values())
        if nested and all(isinstance(item, Mapping) for item in nested):
            return [item for item in nested if isinstance(item, Mapping)]
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return clean_text(value).casefold() in {"1", "true", "yes", "да"}


def unique_visits(source: Any) -> list[Mapping[str, Any]]:
    selected: dict[
        tuple[str, ...], tuple[int, tuple[int, bool], Mapping[str, Any]]
    ] = {}
    order: list[tuple[str, ...]] = []
    for index, visit in enumerate(records(source)):
        identity = _visit_identity(visit)
        quality = _visit_quality(visit)
        current = selected.get(identity)
        if current is None:
            order.append(identity)
            selected[identity] = (index, quality, visit)
            continue

        if quality > current[1]:
            merged = _merge_missing(visit, current[2])
            is_original = quality[1] or current[1][1]
        else:
            merged = _merge_missing(current[2], visit)
            is_original = current[1][1] or quality[1]
        selected[identity] = (
            current[0],
            (_completeness_score(merged), is_original),
            merged,
        )
    return [selected[identity][2] for identity in order]


def _visit_identity(visit: Mapping[str, Any]) -> tuple[str, ...]:
    visit_id = clean_text(first(visit, "id_priema", "visit_id", "appointment_id", "id"))
    if visit_id:
        canonical_id = re.sub(r"[_-]dup(?:licate)?$", "", visit_id, flags=re.IGNORECASE)
        return ("id", canonical_id.casefold())

    doctor = as_mapping(first(visit, "VRACH", "vrach", "doctor", "physician"))
    diagnosis = as_mapping(
        first(visit, "diagnoz_priema", "diagnosis", "diagnoz", "visit_diagnosis")
    )
    return (
        "content",
        normalize_date(first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA"))
        or "",
        clean_text(first(doctor, "fio_doc", "FIO", "fio", "name")).casefold(),
        clean_text(
            first(diagnosis, "osnovnoy_txt", "diagnosis", "diagnoz", "name")
        ).casefold(),
        clean_text(
            first(visit, "JALOBY_TXT", "jaloby_txt", "complaints", "jaloby")
        ).casefold(),
    )


def _visit_quality(visit: Mapping[str, Any]) -> tuple[int, bool]:
    visit_id = clean_text(first(visit, "id_priema", "visit_id", "appointment_id", "id"))
    is_original = not bool(
        re.search(r"[_-]dup(?:licate)?$", visit_id, flags=re.IGNORECASE)
    )
    return _completeness_score(visit), is_original


def _completeness_score(value: Any) -> int:
    if isinstance(value, Mapping):
        return sum(_completeness_score(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return sum(_completeness_score(item) for item in value)
    return int(has_value(value))


def _merge_missing(preferred: Any, fallback: Any) -> Any:
    if isinstance(preferred, Mapping) and isinstance(fallback, Mapping):
        result = dict(preferred)
        for key, fallback_value in fallback.items():
            if key in result:
                result[key] = _merge_missing(result[key], fallback_value)
            else:
                result[key] = fallback_value
        return result
    if isinstance(preferred, list) and isinstance(fallback, list):
        result = list(preferred)
        for item in fallback:
            if item not in result:
                result.append(item)
        return result
    return preferred if has_value(preferred) else fallback


def deduplicate(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
