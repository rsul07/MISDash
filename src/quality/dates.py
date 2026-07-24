"""Independent supported-date fidelity invariant."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from datetime import date, datetime, timezone
from typing import Any

from src.contracts.patient.v1 import PatientRecord

from .common import has_value, mapping_list, valid_bp, valid_number
from .counts import canonical_visit_id
from .models import QualityCheck


def date_fidelity_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    comparisons, unsupported_count = _date_comparisons(data, record)
    mismatches = [
        f"{label}: expected={expected!s}, actual={actual!s}"
        for label, expected, actual in comparisons
        if not _same_clinical_date(expected, actual)
    ]
    return QualityCheck(
        name="dates.supported_values_preserved",
        passed=not mismatches,
        description=(
            "Supported generated encounter, laboratory, instrumental and "
            "diary dates remain non-null and preserve their date or instant."
        ),
        expected={"supported_date_values": len(comparisons)},
        actual={
            "matched_values": len(comparisons) - len(mismatches),
            "mismatch_count": len(mismatches),
            "unsupported_values_skipped": unsupported_count,
        },
        evidence=(
            f"checked_supported_dates={len(comparisons)}",
            f"unsupported_dates_skipped={unsupported_count}",
            *mismatches[:6],
        ),
    )


def _date_comparisons(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> tuple[list[tuple[str, date | datetime, Any]], int]:
    comparisons: list[tuple[str, date | datetime, Any]] = []
    unsupported = 0

    visit_dates: dict[str, list[date | datetime]] = {}
    for index, visit in enumerate(mapping_list(data.get("PRIEMY_VRACHA"))):
        parsed = _parse_supported_date(visit.get("dt_priem"))
        if parsed is None:
            unsupported += 1
            continue
        visit_dates.setdefault(
            canonical_visit_id(visit, index),
            [],
        ).append(parsed)
    encounter_by_id = {
        encounter.id.casefold(): encounter for encounter in record.encounters
    }
    for identity, candidates in visit_dates.items():
        expected = max(candidates, key=_date_precision)
        encounter = encounter_by_id.get(identity)
        comparisons.append(
            (
                f"encounter[{identity}].occurred_at",
                expected,
                encounter.occurred_at if encounter is not None else None,
            )
        )

    reports_by_path = {
        (report.source.path, report.category): report
        for report in record.diagnostic_reports
    }
    for index, panel in enumerate(
        mapping_list(data.get("lab_issledovaniya"))
    ):
        report = reports_by_path.get(
            (f"lab_issledovaniya[{index}]", "laboratory")
        )
        unsupported += _append_supported_date(
            comparisons,
            f"laboratory[{index}].effective_at",
            panel.get("data_vzyatia"),
            report.effective_at if report is not None else None,
        )
        unsupported += _append_supported_date(
            comparisons,
            f"laboratory[{index}].issued_at",
            panel.get("data_gotovnosti"),
            report.issued_at if report is not None else None,
        )
    for index, item in enumerate(
        mapping_list(data.get("instrumental_issled"))
    ):
        report = reports_by_path.get(
            (f"instrumental_issled[{index}]", "instrumental")
        )
        unsupported += _append_supported_date(
            comparisons,
            f"instrumental[{index}].effective_at",
            item.get("DT_ISSLED"),
            report.effective_at if report is not None else None,
        )

    observations = {
        (observation.source.path, observation.coding.code): observation
        for observation in record.observations
    }
    diary = data.get("dnevnik_samokontrolya")
    diary = diary if isinstance(diary, Mapping) else {}
    for index, item in enumerate(
        mapping_list(diary.get("AD_izmereniya"))
    ):
        path = f"dnevnik_samokontrolya.AD_izmereniya[{index}]"
        expected_codes: list[str] = []
        if valid_bp(item.get("sys"), item.get("dia")):
            expected_codes.append("blood-pressure")
        if valid_number(item.get("pulse"), 20, 250) is not None:
            expected_codes.append("heart-rate")
        for code in expected_codes:
            observation = observations.get((path, code))
            unsupported += _append_supported_date(
                comparisons,
                f"{path}::{code}",
                item.get("dt"),
                observation.observed_at
                if observation is not None
                else None,
            )
    for index, item in enumerate(mapping_list(diary.get("glikemiya"))):
        if not has_value(item.get("glukoza_mmol")):
            continue
        path = f"dnevnik_samokontrolya.glikemiya[{index}]"
        observation = observations.get((path, "glucose"))
        unsupported += _append_supported_date(
            comparisons,
            f"{path}::glucose",
            item.get("izmereno"),
            observation.observed_at if observation is not None else None,
        )
    return comparisons, unsupported


def _append_supported_date(
    output: list[tuple[str, date | datetime, Any]],
    label: str,
    raw: Any,
    actual: Any,
) -> int:
    expected = _parse_supported_date(raw)
    if expected is None:
        return int(has_value(raw))
    output.append((label, expected, actual))
    return 0


def _parse_supported_date(value: Any) -> date | datetime | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return _numeric_date(value)
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw or raw.casefold() in {
        "-",
        "—",
        "n/a",
        "null",
        "none",
        "нет данных",
        "н/д",
    }:
        return None
    if re.fullmatch(r"\d{8}", raw):
        try:
            return datetime.strptime(raw, "%Y%m%d").date()
        except ValueError:
            return None
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        try:
            return _numeric_date(float(raw))
        except ValueError:
            return None
    iso_candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(iso_candidate)
        return parsed if _contains_time(raw) else parsed.date()
    except ValueError:
        pass
    for date_format, has_time in (
        ("%d.%m.%Y", False),
        ("%d/%m/%Y", False),
        ("%d.%m.%y", False),
        ("%d/%m/%y", False),
        ("%d.%m.%Y %H:%M", True),
        ("%d/%m/%Y %H:%M", True),
        ("%d.%m.%y %H:%M", True),
        ("%d/%m/%y %H:%M", True),
    ):
        try:
            parsed = datetime.strptime(raw, date_format)
            return parsed if has_time else parsed.date()
        except ValueError:
            continue
    return None


def _numeric_date(value: int | float) -> date | datetime | None:
    number = float(value)
    if not math.isfinite(number):
        return None
    integer = int(number)
    if number.is_integer() and 1000 <= integer <= 9999:
        return None
    if number.is_integer() and 10_000_000 <= integer <= 99_999_999:
        try:
            return datetime.strptime(str(integer), "%Y%m%d").date()
        except ValueError:
            return None
    while abs(number) > 10_000_000_000:
        number /= 1000
    try:
        return datetime.fromtimestamp(number, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _contains_time(value: str) -> bool:
    return "T" in value or bool(re.search(r"\s\d{1,2}:\d{2}", value))


def _date_precision(value: date | datetime) -> int:
    return 2 if isinstance(value, datetime) else 1


def _same_clinical_date(
    expected: date | datetime,
    actual: Any,
) -> bool:
    if actual is None or not isinstance(actual, date):
        return False
    if isinstance(expected, datetime):
        if not isinstance(actual, datetime):
            return False
        if expected.tzinfo is None and actual.tzinfo is None:
            return expected == actual
        return _as_utc(expected) == _as_utc(actual)
    actual_date = actual.date() if isinstance(actual, datetime) else actual
    return expected == actual_date


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

