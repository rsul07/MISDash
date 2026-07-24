"""Orchestration for generated-export quality invariants."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from pathlib import Path
from time import perf_counter
from typing import Any

from src.contracts.patient.v1 import PatientRecord
from src.generator import GenerationConfig
from src.parser import MISParser

from .common import medical_data
from .counts import count_checks
from .fidelity import fidelity_checks
from .integrity import integrity_checks
from .models import CaseQualityReport, QualityCheck
from .provenance import provenance_checks


def assess_generated_case(config: GenerationConfig) -> CaseQualityReport:
    """Generate one export and run it through the public parser boundary."""

    from src.generator import generate_export

    return assess_export(generate_export(config), config=config)


def assess_export(
    payload: Mapping[str, Any],
    *,
    config: GenerationConfig,
) -> CaseQualityReport:
    """Parse an in-memory dirty export and evaluate all quality invariants."""

    started_at = perf_counter()
    try:
        record = _parse_payload(payload)
    except Exception as error:
        return CaseQualityReport(
            config=config,
            checks=(
                QualityCheck(
                    name="parse.success",
                    passed=False,
                    description=(
                        "Dirty JSON is accepted as PatientRecord v1."
                    ),
                    evidence=(f"{type(error).__name__}: {error}",),
                    expected="PatientRecord v1",
                    actual=type(error).__name__,
                ),
            ),
            duration_seconds=perf_counter() - started_at,
        )

    report = assess_record(
        payload,
        record,
        config=config,
    )
    return CaseQualityReport(
        config=report.config,
        checks=report.checks,
        duration_seconds=perf_counter() - started_at,
    )


def assess_record(
    payload: Mapping[str, Any],
    record: PatientRecord,
    *,
    config: GenerationConfig,
    duration_seconds: float = 0.0,
) -> CaseQualityReport:
    """Evaluate an already parsed record, useful for focused diagnostics."""

    data = medical_data(payload)
    checks = (
        QualityCheck(
            name="parse.success",
            passed=True,
            description="A validated PatientRecord v1 was supplied.",
            evidence=(
                f"schema_version={record.schema_version}",
                f"patient_id={record.patient.id}",
            ),
            expected="PatientRecord v1",
            actual=f"PatientRecord {record.schema_version}",
        ),
        *count_checks(data, record),
        *integrity_checks(data, record),
        *provenance_checks(data, record),
        *fidelity_checks(data, record),
    )
    return CaseQualityReport(
        config=config,
        checks=checks,
        duration_seconds=duration_seconds,
    )


def _parse_payload(payload: Mapping[str, Any]) -> PatientRecord:
    with tempfile.TemporaryDirectory(prefix="mis-dash-quality-") as directory:
        path = Path(directory) / "generated.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        return MISParser(path).parse_record()
