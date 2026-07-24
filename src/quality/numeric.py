"""Independent numeric-fidelity invariant."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from src.contracts.patient.v1 import PatientRecord

from .common import mapping_list, parse_number, valid_number
from .counts import included_lab_result
from .models import QualityCheck


def numeric_fidelity_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    expected = _expected_numeric_values(data)
    actual = _actual_numeric_values(record)
    mismatches = [
        (
            f"{path}::{metric}: expected={value}, "
            f"actual={actual.get((path, metric))!r}"
        )
        for (path, metric), value in expected.items()
        if not _same_number(value, actual.get((path, metric)))
    ]
    return QualityCheck(
        name="values.numeric_fidelity",
        passed=not mismatches,
        description=(
            "Generated laboratory and self-monitoring numbers retain their "
            "value after independent decimal parsing."
        ),
        expected={"numeric_values": len(expected)},
        actual={
            "matched_values": len(expected) - len(mismatches),
            "mismatch_count": len(mismatches),
        },
        evidence=(
            f"checked_numeric_values={len(expected)}",
            *mismatches[:6],
        ),
    )


def _expected_numeric_values(
    data: Mapping[str, Any],
) -> dict[tuple[str, str], float]:
    result: dict[tuple[str, str], float] = {}
    for panel_index, panel in enumerate(
        mapping_list(data.get("lab_issledovaniya"))
    ):
        for result_index, item in enumerate(
            mapping_list(panel.get("REZULTATY"))
        ):
            if not included_lab_result(item):
                continue
            value = parse_number(item.get("REZULT"))
            if value is not None:
                path = (
                    f"lab_issledovaniya[{panel_index}]."
                    f"REZULTATY[{result_index}]"
                )
                result[(path, "laboratory-result")] = value

    diary = data.get("dnevnik_samokontrolya")
    diary = diary if isinstance(diary, Mapping) else {}
    for index, item in enumerate(
        mapping_list(diary.get("AD_izmereniya"))
    ):
        path = f"dnevnik_samokontrolya.AD_izmereniya[{index}]"
        systolic = valid_number(item.get("sys"), 60, 300)
        diastolic = valid_number(item.get("dia"), 30, 200)
        if (
            systolic is not None
            and diastolic is not None
            and systolic > diastolic
        ):
            result[(path, "systolic")] = systolic
            result[(path, "diastolic")] = diastolic
        heart_rate = valid_number(item.get("pulse"), 20, 250)
        if heart_rate is not None:
            result[(path, "heart-rate")] = heart_rate
    for index, item in enumerate(mapping_list(diary.get("glikemiya"))):
        value = parse_number(item.get("glukoza_mmol"))
        if value is not None:
            path = f"dnevnik_samokontrolya.glikemiya[{index}]"
            result[(path, "glucose")] = value
    return result


def _actual_numeric_values(
    record: PatientRecord,
) -> dict[tuple[str, str], float]:
    result: dict[tuple[str, str], float] = {}
    for observation in record.observations:
        path = observation.source.path
        if not path:
            continue
        if observation.category == "laboratory":
            value = (
                observation.value.value
                if observation.value is not None
                else None
            )
            number = _canonical_number(value)
            if number is not None:
                result[(path, "laboratory-result")] = number
        elif observation.coding.code == "blood-pressure":
            for component in observation.components:
                number = _canonical_number(component.value.value)
                if number is None:
                    continue
                if component.coding.code in {"systolic", "diastolic"}:
                    result[(path, component.coding.code)] = number
        elif observation.coding.code in {"heart-rate", "glucose"}:
            value = (
                observation.value.value
                if observation.value is not None
                else None
            )
            number = _canonical_number(value)
            if number is not None:
                result[(path, observation.coding.code)] = number
    return result


def _canonical_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _same_number(expected: float, actual: float | None) -> bool:
    return actual is not None and math.isclose(
        expected,
        actual,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )
