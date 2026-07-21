"""Tests for deterministic and bounded summarizer context."""

from __future__ import annotations

from datetime import date, datetime, timezone

from src.backend import DashboardService
from src.contracts.patient.v1 import (
    Condition,
    DiagnosticReport,
    Encounter,
    Observation,
    Patient,
    PatientRecord,
)
from src.contracts.patient.v1.common import Coding, Quantity, SourceReference
from src.summarizer import ContextLimits, build_summary_context


SOURCE = SourceReference(block="test")


def _record(
    *,
    encounters: list[Encounter] | None = None,
    reports: list[DiagnosticReport] | None = None,
    observations: list[Observation] | None = None,
) -> PatientRecord:
    return PatientRecord(
        patient=Patient(
            id="patient-1",
            full_name="Synthetic Patient",
            source=SOURCE,
        ),
        encounters=encounters or [],
        diagnostic_reports=reports or [],
        observations=observations or [],
    )


def test_context_is_empty_without_clinical_data() -> None:
    record = _record()

    context = build_summary_context(
        record,
        DashboardService().build(
            record,
            generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )

    assert context.facts == []
    assert context.source_ids == set()


def test_context_marks_dashboard_facts_as_already_visible() -> None:
    record = PatientRecord(
        patient=Patient(
            id="patient-1",
            full_name="Synthetic Patient",
            source=SOURCE,
        ),
        conditions=[
            Condition(
                id="condition-1",
                source=SOURCE,
                coding=Coding(code="I10", display="Гипертензия"),
            )
        ],
    )

    context = build_summary_context(record, DashboardService().build(record))

    assert context.facts[0].source_id == "condition:0"
    assert context.facts[0].visible_on_dashboard is True


def test_context_limits_records_and_truncates_free_text() -> None:
    encounters = [
        Encounter(
            id=f"visit-{index}",
            source=SOURCE,
            occurred_at=date(2020, 1, index + 1),
            complaints="x" * 30,
        )
        for index in range(15)
    ]
    reports = [
        DiagnosticReport(
            id=f"report-{index}",
            source=SOURCE,
            category="instrumental",
            coding=Coding(display="ЭКГ"),
            effective_at=date(2020, 2, index + 1),
            conclusion="Синусовый ритм",
        )
        for index in range(12)
    ]
    record = _record(encounters=encounters, reports=reports)
    dashboard = DashboardService().build(record)

    context = build_summary_context(
        record,
        dashboard,
        limits=ContextLimits(field_characters=12),
    )

    assert len([fact for fact in context.facts if fact.kind == "encounter"]) == 12
    assert len([fact for fact in context.facts if fact.kind == "diagnostic_report"]) == 10
    assert context.omitted_records == 5
    assert context.truncated_fields == 22
    assert context.facts[0].source_id == "encounter:visit-14"


def test_context_sends_metric_summary_instead_of_raw_observations() -> None:
    observations = [
        Observation(
            id=f"glucose-{index}",
            source=SOURCE,
            observed_at=observed_at,
            category="laboratory",
            coding=Coding(code="glucose", display="Глюкоза"),
            value=Quantity(value=value, unit="mmol/L"),
        )
        for index, (observed_at, value) in enumerate(
            ((date(2024, 1, 1), 5.0), (date(2025, 1, 1), 6.5))
        )
    ]
    record = _record(observations=observations)

    context = build_summary_context(record, DashboardService().build(record))

    assert len(context.facts) == 1
    metric = context.facts[0]
    assert metric.source_id == "metric:glucose"
    assert metric.visible_on_dashboard is False
    assert "последнее значение: 6.5 mmol/L от 2025-01-01" in metric.text
    assert "среднее за последние 12 месяцев: 6.50 mmol/L" in metric.text
    assert "среднее за предыдущие 12 месяцев: 5.00 mmol/L" in metric.text
    assert "изменение средних: +1.50 mmol/L" in metric.text
    assert "glucose-0" not in metric.text
