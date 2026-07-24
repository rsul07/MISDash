"""Focused tests for generator-to-parser quality invariants."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from src.generator import GenerationConfig, generate_export
from src.parser.canonical.builder import build_patient_record
from src.quality import assess_export, assess_record


@pytest.fixture(scope="module")
def config() -> GenerationConfig:
    return GenerationConfig(seed=99, years=1, light=True)


@pytest.fixture(scope="module")
def generated_payload(
    config: GenerationConfig,
) -> dict[str, Any]:
    return generate_export(config)


def test_generated_case_passes_named_invariants_with_evidence(
    config: GenerationConfig,
    generated_payload: dict[str, Any],
) -> None:
    report = assess_export(generated_payload, config=config)

    assert report.passed
    assert {
        check.name for check in report.checks
    } == {
        "parse.success",
        "counts.encounters",
        "counts.laboratory",
        "counts.instrumental",
        "counts.self_monitoring",
        "canonical.ids_unique_by_type",
        "references.integrity",
        "provenance.paths_resolve",
        "provenance.source_ids_match",
        "laboratory.comments_preserved",
        "values.numeric_finite",
        "exclusions.intentional",
        "values.numeric_fidelity",
        "dates.supported_values_preserved",
    }
    assert all(check.evidence for check in report.checks)
    assert report.check("counts.encounters").actual == 4
    assert report.check("counts.encounters").expected == 4


def test_deleted_lab_result_is_accounted_for_and_not_emitted(
    config: GenerationConfig,
    generated_payload: dict[str, Any],
) -> None:
    payload = _clone(generated_payload)
    first_result = payload["data"]["lab_issledovaniya"][0]["REZULTATY"][0]
    first_result["is_deleted"] = 1
    first_result["comment_lab"] = "не должен попасть в контракт"

    report = assess_export(payload, config=config)

    assert report.passed
    lab_check = report.check("counts.laboratory")
    assert "deleted_results=1" in lab_check.evidence
    exclusion_check = report.check("exclusions.intentional")
    assert "deleted_results_accounted=1" in exclusion_check.evidence
    assert report.check("laboratory.comments_preserved").expected == {
        "comment_count": _included_comment_count(payload)
    }


def test_audit_detects_broken_reference_and_non_finite_value(
    config: GenerationConfig,
    generated_payload: dict[str, Any],
) -> None:
    record = build_patient_record(generated_payload["data"])
    record.medications[0].encounter_id = "missing-encounter"
    record.patient.height_cm = float("nan")

    report = assess_record(
        generated_payload,
        record,
        config=config,
    )

    assert not report.passed
    reference_check = report.check("references.integrity")
    assert not reference_check.passed
    assert any(
        "missing encounter" in evidence
        for evidence in reference_check.evidence
    )
    finite_check = report.check("values.numeric_finite")
    assert not finite_check.passed
    assert any(
        "record.patient.height_cm=nan" in evidence
        for evidence in finite_check.evidence
    )


def test_audit_detects_unresolvable_provenance_path(
    config: GenerationConfig,
    generated_payload: dict[str, Any],
) -> None:
    record = build_patient_record(generated_payload["data"])
    record.encounters[0].source.path = "PRIEMY_VRACHA[99999]"

    report = assess_record(
        generated_payload,
        record,
        config=config,
    )

    check = report.check("provenance.paths_resolve")
    assert not check.passed
    assert any("invalid index 99999" in item for item in check.evidence)


def test_audit_detects_changed_numeric_value(
    config: GenerationConfig,
    generated_payload: dict[str, Any],
) -> None:
    record = build_patient_record(generated_payload["data"])
    observation = next(
        item
        for item in record.observations
        if item.category == "laboratory"
        and item.value is not None
        and isinstance(item.value.value, (int, float))
    )
    observation.value.value = float(observation.value.value) + 1.0

    report = assess_record(
        generated_payload,
        record,
        config=config,
    )

    check = report.check("values.numeric_fidelity")
    assert not check.passed
    assert any("expected=" in item for item in check.evidence)


def test_audit_detects_changed_supported_date(
    config: GenerationConfig,
    generated_payload: dict[str, Any],
) -> None:
    record = build_patient_record(generated_payload["data"])
    record.encounters[0].occurred_at = date(1900, 1, 1)

    report = assess_record(
        generated_payload,
        record,
        config=config,
    )

    check = report.check("dates.supported_values_preserved")
    assert not check.passed
    assert any("1900-01-01" in item for item in check.evidence)


def _clone(value: dict[str, Any]) -> dict[str, Any]:
    import copy

    return copy.deepcopy(value)


def _included_comment_count(payload: dict[str, Any]) -> int:
    return sum(
        bool(result.get("comment_lab")) and not result.get("is_deleted")
        for panel in payload["data"]["lab_issledovaniya"]
        for result in panel["REZULTATY"]
    )
