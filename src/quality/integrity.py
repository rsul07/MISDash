"""Canonical identity, reference, numeric and exclusion invariants."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from src.contracts.patient.v1 import PatientRecord

from .common import (
    IGNORED_SOURCE_BLOCKS,
    mapping_list,
    source_references,
    top_level_block,
    truthy_flag,
)
from .models import QualityCheck


def integrity_checks(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> tuple[QualityCheck, ...]:
    return (
        _unique_ids_check(record),
        _reference_integrity_check(record),
        _finite_numbers_check(record),
        _intentional_exclusions_check(data, record),
    )


def _unique_ids_check(record: PatientRecord) -> QualityCheck:
    collections = {
        "family_history": record.family_history,
        "allergies": record.allergies,
        "conditions": record.conditions,
        "medications": record.medications,
        "encounters": record.encounters,
        "observations": record.observations,
        "procedures": record.procedures,
        "hospitalizations": record.hospitalizations,
        "immunizations": record.immunizations,
        "diagnostic_reports": record.diagnostic_reports,
    }
    duplicates: dict[str, list[str]] = {}
    for name, items in collections.items():
        counts = Counter(item.id for item in items)
        repeated = sorted(
            identifier
            for identifier, count in counts.items()
            if count > 1
        )
        if repeated:
            duplicates[name] = repeated

    evidence = [
        f"{name}={len(items)}"
        for name, items in collections.items()
    ]
    evidence.extend(
        f"{name}: duplicate={','.join(identifiers[:5])}"
        for name, identifiers in duplicates.items()
    )
    return QualityCheck(
        name="canonical.ids_unique_by_type",
        passed=not duplicates,
        description=(
            "Canonical IDs are unique within each typed resource "
            "collection; different resource types have separate namespaces."
        ),
        expected="no duplicate IDs within a resource type",
        actual={"duplicates_by_type": duplicates},
        evidence=tuple(evidence),
    )


def _reference_integrity_check(record: PatientRecord) -> QualityCheck:
    encounter_by_id = {item.id: item for item in record.encounters}
    medication_by_id = {item.id: item for item in record.medications}
    observation_by_id = {item.id: item for item in record.observations}
    report_by_id = {item.id: item for item in record.diagnostic_reports}
    errors: list[str] = []

    for encounter in record.encounters:
        for medication_id in encounter.medication_ids:
            medication = medication_by_id.get(medication_id)
            if medication is None:
                errors.append(
                    f"encounter {encounter.id} -> missing medication "
                    f"{medication_id}"
                )
            elif medication.encounter_id != encounter.id:
                errors.append(
                    f"medication {medication.id} points to "
                    f"{medication.encounter_id}, expected {encounter.id}"
                )
    for medication in record.medications:
        encounter = encounter_by_id.get(medication.encounter_id or "")
        if encounter is None:
            errors.append(
                f"medication {medication.id} -> missing encounter "
                f"{medication.encounter_id}"
            )
        elif medication.id not in encounter.medication_ids:
            errors.append(
                f"encounter {encounter.id} does not list medication "
                f"{medication.id}"
            )
    for observation in record.observations:
        if (
            observation.encounter_id is not None
            and observation.encounter_id not in encounter_by_id
        ):
            errors.append(
                f"observation {observation.id} -> missing encounter "
                f"{observation.encounter_id}"
            )
        if observation.report_id is not None:
            report = report_by_id.get(observation.report_id)
            if report is None:
                errors.append(
                    f"observation {observation.id} -> missing report "
                    f"{observation.report_id}"
                )
            elif observation.id not in report.observation_ids:
                errors.append(
                    f"report {report.id} does not list observation "
                    f"{observation.id}"
                )
    for report in record.diagnostic_reports:
        for observation_id in report.observation_ids:
            observation = observation_by_id.get(observation_id)
            if observation is None:
                errors.append(
                    f"report {report.id} -> missing observation "
                    f"{observation_id}"
                )
            elif observation.report_id != report.id:
                errors.append(
                    f"observation {observation.id} points to "
                    f"{observation.report_id}, expected {report.id}"
                )

    return QualityCheck(
        name="references.integrity",
        passed=not errors,
        description=(
            "Encounter, medication, observation and diagnostic-report "
            "references are bidirectionally consistent."
        ),
        expected="all references resolve",
        actual={"error_count": len(errors)},
        evidence=(
            f"encounters={len(encounter_by_id)}",
            f"medications={len(medication_by_id)}",
            f"observations={len(observation_by_id)}",
            f"reports={len(report_by_id)}",
            *errors[:6],
        ),
    )


def _finite_numbers_check(record: PatientRecord) -> QualityCheck:
    invalid: list[str] = []
    _find_non_finite(
        record.model_dump(mode="python"),
        path="record",
        output=invalid,
    )
    return QualityCheck(
        name="values.numeric_finite",
        passed=not invalid,
        description="Every canonical floating-point value is finite.",
        expected="no NaN or infinity",
        actual={"invalid_count": len(invalid)},
        evidence=(f"checked_record={record.patient.id}", *invalid[:6]),
    )


def _find_non_finite(
    value: Any,
    *,
    path: str,
    output: list[str],
) -> None:
    if isinstance(value, float):
        if not math.isfinite(value):
            output.append(f"{path}={value}")
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _find_non_finite(
                nested,
                path=f"{path}.{key}",
                output=output,
            )
        return
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, nested in enumerate(value):
            _find_non_finite(
                nested,
                path=f"{path}[{index}]",
                output=output,
            )


def _intentional_exclusions_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    used_ignored_sources = [
        f"{label}: {source.block}"
        for label, source in source_references(record)
        if top_level_block(source.block) in IGNORED_SOURCE_BLOCKS
    ]
    deleted_paths = _deleted_lab_paths(data)
    emitted_deleted_paths = [
        observation.source.path or ""
        for observation in record.observations
        if observation.source.path in deleted_paths
    ]
    errors = [*used_ignored_sources, *emitted_deleted_paths]
    present_blocks = [
        block for block in IGNORED_SOURCE_BLOCKS if block in data
    ]
    return QualityCheck(
        name="exclusions.intentional",
        passed=not errors,
        description=(
            "Service/migration blocks and explicitly deleted laboratory "
            "results are excluded from the canonical clinical record."
        ),
        expected={
            "ignored_blocks": list(IGNORED_SOURCE_BLOCKS),
            "deleted_results_excluded": len(deleted_paths),
        },
        actual={
            "present_ignored_blocks": present_blocks,
            "unexpected_sources": len(errors),
        },
        evidence=(
            f"ignored_blocks_present={','.join(present_blocks) or 'none'}",
            f"deleted_results_accounted={len(deleted_paths)}",
            *errors[:6],
        ),
    )


def _deleted_lab_paths(data: Mapping[str, Any]) -> set[str]:
    result: set[str] = set()
    for panel_index, panel in enumerate(
        mapping_list(data.get("lab_issledovaniya"))
    ):
        for result_index, item in enumerate(
            mapping_list(panel.get("REZULTATY"))
        ):
            if truthy_flag(item.get("is_deleted")):
                result.add(
                    f"lab_issledovaniya[{panel_index}]."
                    f"REZULTATY[{result_index}]"
                )
    return result

