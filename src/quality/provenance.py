"""Source-path, source-ID and retained-comment invariants."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.contracts.patient.v1 import PatientRecord

from .common import (
    clean_scalar,
    mapping_list,
    resolve_path,
    source_id_candidates,
    source_references,
)
from .counts import included_lab_result
from .models import QualityCheck


def provenance_checks(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> tuple[QualityCheck, ...]:
    return (
        *_source_checks(data, record),
        _laboratory_comments_check(data, record),
    )


def _source_checks(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> tuple[QualityCheck, QualityCheck]:
    path_errors: list[str] = []
    source_id_errors: list[str] = []
    paths_checked = 0
    source_ids_checked = 0
    for label, source in source_references(record):
        if not source.path:
            path_errors.append(f"{label}: empty source.path")
            continue
        paths_checked += 1
        resolution = resolve_path(data, source.path)
        if isinstance(resolution, str):
            path_errors.append(f"{label}: {resolution}")
            continue
        _, ancestors = resolution
        if not source.path.startswith(source.block):
            path_errors.append(
                f"{label}: block={source.block!r} is not a path prefix"
            )
        if source.source_id is None:
            continue
        source_ids_checked += 1
        candidates = {
            normalized
            for ancestor in reversed(ancestors)
            for normalized in source_id_candidates(ancestor)
        }
        if source.source_id.casefold() not in candidates:
            source_id_errors.append(
                f"{label}: source_id={source.source_id!r}, "
                f"path={source.path!r}"
            )

    return (
        QualityCheck(
            name="provenance.paths_resolve",
            passed=not path_errors,
            description=(
                "Every canonical source.path resolves inside the original "
                "medical-data object and agrees with source.block."
            ),
            expected="all source paths resolve",
            actual={"error_count": len(path_errors)},
            evidence=(f"checked_paths={paths_checked}", *path_errors[:6]),
        ),
        QualityCheck(
            name="provenance.source_ids_match",
            passed=not source_id_errors,
            description=(
                "Every non-empty source_id occurs at the resolved source "
                "node or one of its parent records."
            ),
            expected="all applicable source IDs match",
            actual={"error_count": len(source_id_errors)},
            evidence=(
                f"checked_source_ids={source_ids_checked}",
                *source_id_errors[:6],
            ),
        ),
    )


def _laboratory_comments_check(
    data: Mapping[str, Any],
    record: PatientRecord,
) -> QualityCheck:
    expected: dict[str, str] = {}
    panels = mapping_list(data.get("lab_issledovaniya"))
    for panel_index, panel in enumerate(panels):
        for result_index, item in enumerate(
            mapping_list(panel.get("REZULTATY"))
        ):
            if not included_lab_result(item):
                continue
            comment = clean_scalar(
                item.get("comment_lab")
                or item.get("comment")
                or item.get("note")
            )
            if comment:
                expected[
                    f"lab_issledovaniya[{panel_index}]."
                    f"REZULTATY[{result_index}]"
                ] = comment

    actual = {
        observation.source.path: observation.context.get(
            "laboratory_comment", ""
        )
        for observation in record.observations
        if observation.category == "laboratory"
        and observation.source.path in expected
    }
    mismatches = [
        path
        for path, comment in expected.items()
        if clean_scalar(actual.get(path)) != comment
    ]
    return QualityCheck(
        name="laboratory.comments_preserved",
        passed=not mismatches,
        description=(
            "Clinical laboratory comments such as haemolysis, lipaemia or "
            "repeat-test warnings remain attached to their observation."
        ),
        expected={"comment_count": len(expected)},
        actual={
            "preserved_count": len(expected) - len(mismatches),
            "mismatch_count": len(mismatches),
        },
        evidence=(
            f"raw_comments={len(expected)}",
            *[f"missing_or_changed={path}" for path in mismatches[:6]],
        ),
    )
