"""Expected raw-to-canonical resource count invariants."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from src.contracts.patient.v1 import PatientRecord

from .common import (
    clean_scalar,
    has_value,
    mapping_list,
    truthy_flag,
    valid_bp,
    valid_number,
)
from .models import QualityCheck


def count_checks(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> tuple[QualityCheck, ...]:
    return (
        _encounter_count_check(data, record),
        _laboratory_count_check(data, record),
        _instrumental_count_check(data, record),
        _diary_count_check(data, record),
    )


def included_lab_result(result: Mapping[str, Any]) -> bool:
    return bool(
        not truthy_flag(result.get("is_deleted"))
        and clean_scalar(result.get("pokazatel"))
    )


def deleted_lab_result_count(
    panels: Sequence[Mapping[str, Any]],
) -> int:
    return sum(
        truthy_flag(result.get("is_deleted"))
        for panel in panels
        for result in mapping_list(panel.get("REZULTATY"))
    )


def _encounter_count_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    visits = mapping_list(data.get("PRIEMY_VRACHA"))
    identities = {
        canonical_visit_id(visit, index)
        for index, visit in enumerate(visits)
    }
    expected = len(identities)
    actual = len(record.encounters)
    return QualityCheck(
        name="counts.encounters",
        passed=actual == expected,
        description="Visit records are deduplicated by their canonical MIS ID.",
        expected=expected,
        actual=actual,
        evidence=(
            f"raw_visits={len(visits)}",
            f"deduplicated_visits={expected}",
            f"accounted_duplicates={len(visits) - expected}",
        ),
    )


def canonical_visit_id(
    visit: Mapping[str, Any],
    index: int,
) -> str:
    raw = clean_scalar(visit.get("id_priema"))
    if raw:
        return re.sub(
            r"[_-]dup(?:licate)?$",
            "",
            raw,
            flags=re.IGNORECASE,
        ).casefold()
    return f"missing-id-{index}"


def _laboratory_count_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    panels = mapping_list(data.get("lab_issledovaniya"))
    expected_results = sum(
        included_lab_result(result)
        for panel in panels
        for result in mapping_list(panel.get("REZULTATY"))
    )
    expected = {
        "reports": len(panels),
        "results": expected_results,
    }
    actual = {
        "reports": sum(
            report.category == "laboratory"
            for report in record.diagnostic_reports
        ),
        "results": sum(
            observation.category == "laboratory"
            for observation in record.observations
        ),
    }
    return QualityCheck(
        name="counts.laboratory",
        passed=actual == expected,
        description=(
            "Each laboratory panel and every non-deleted named result are "
            "represented canonically."
        ),
        expected=expected,
        actual=actual,
        evidence=(
            f"raw_panels={len(panels)}",
            f"included_results={expected_results}",
            f"deleted_results={deleted_lab_result_count(panels)}",
        ),
    )


def _instrumental_count_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    expected = sum(
        bool(clean_scalar(item.get("issledovanie")))
        for item in mapping_list(data.get("instrumental_issled"))
    )
    actual = sum(
        report.category == "instrumental"
        for report in record.diagnostic_reports
    )
    return QualityCheck(
        name="counts.instrumental",
        passed=actual == expected,
        description="Named instrumental reports are retained.",
        expected=expected,
        actual=actual,
        evidence=(f"named_raw_reports={expected}",),
    )


def _diary_count_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    diary = data.get("dnevnik_samokontrolya")
    diary = diary if isinstance(diary, Mapping) else {}
    blood_pressure = mapping_list(diary.get("AD_izmereniya"))
    glucose = mapping_list(diary.get("glikemiya"))
    expected = {
        "blood_pressure": sum(
            valid_bp(item.get("sys"), item.get("dia"))
            for item in blood_pressure
        ),
        "heart_rate": sum(
            valid_number(item.get("pulse"), 20, 250) is not None
            for item in blood_pressure
        ),
        "glucose": sum(
            has_value(item.get("glukoza_mmol"))
            for item in glucose
        ),
    }
    diary_observations = [
        observation
        for observation in record.observations
        if (observation.source.path or "").startswith(
            "dnevnik_samokontrolya."
        )
    ]
    actual = {
        "blood_pressure": sum(
            item.coding.code == "blood-pressure"
            for item in diary_observations
        ),
        "heart_rate": sum(
            item.coding.code == "heart-rate"
            for item in diary_observations
        ),
        "glucose": sum(
            item.coding.code == "glucose"
            for item in diary_observations
        ),
    }
    return QualityCheck(
        name="counts.self_monitoring",
        passed=actual == expected,
        description=(
            "Valid blood-pressure, pulse and glucose diary entries are "
            "represented without treating invalid measurements as observations."
        ),
        expected=expected,
        actual=actual,
        evidence=(
            f"raw_bp_rows={len(blood_pressure)}",
            f"raw_glucose_rows={len(glucose)}",
        ),
    )
