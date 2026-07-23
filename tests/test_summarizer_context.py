"""Tests for deterministic and bounded summarizer context."""

from __future__ import annotations

from datetime import date, datetime, timezone

from src.backend import DashboardService
from src.contracts.dashboard.v1 import (
    CalculationInfo,
    DashboardPatient,
    DashboardResponse,
    MetricPoint,
    MetricSeries,
)
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


def test_context_projects_dated_encounter_text_with_stable_source_ids() -> None:
    older = Encounter(
        id="visit-older",
        source=SOURCE,
        occurred_at=date(2025, 11, 10),
        complaints="Одышка при подъёме по лестнице",
        history="Иногда пропускает вечерний приём препарата",
        objective="Пастозность голеней",
        plan="Повторная консультация после обследования",
    )
    newer = Encounter(
        id="visit-newer",
        source=SOURCE,
        occurred_at=date(2026, 1, 15),
        complaints="Одышка стала реже",
        history="Препарат принимает регулярно",
        objective="Отёков нет",
        plan="Контрольный осмотр",
        follow_up_at=date(2026, 2, 1),
    )
    record = _record(encounters=[older, newer])
    dashboard = DashboardService().build(record)

    context = build_summary_context(record, dashboard)
    reordered = build_summary_context(
        _record(encounters=[newer, older]),
        dashboard,
    )

    assert context == reordered
    assert [fact.source_id for fact in context.facts] == [
        "encounter:visit-newer",
        "encounter:visit-older",
    ]
    latest = context.facts[0]
    assert latest.occurred_at == "2026-01-15"
    assert latest.text == (
        "жалобы: Одышка стала реже; "
        "анамнез: Препарат принимает регулярно; "
        "объективный статус: Отёков нет; "
        "план: Контрольный осмотр; "
        "повторный приём: 2026-02-01"
    )


def test_context_projects_dated_instrumental_report_text() -> None:
    record = _record(
        reports=[
            DiagnosticReport(
                id="echo",
                source=SOURCE,
                category="instrumental",
                coding=Coding(display="ЭхоКГ"),
                effective_at=date(2025, 12, 1),
                conclusion="Клапанных нарушений не выявлено",
            ),
            DiagnosticReport(
                id="ecg",
                source=SOURCE,
                category="instrumental",
                coding=Coding(display="ЭКГ"),
                issued_at=date(2026, 1, 10),
                conclusion="Синусовый ритм",
            ),
            DiagnosticReport(
                id="laboratory",
                source=SOURCE,
                category="laboratory",
                coding=Coding(display="Биохимия"),
                effective_at=date(2026, 1, 20),
                conclusion="Показатели без особенностей",
            ),
            DiagnosticReport(
                id="empty",
                source=SOURCE,
                category="instrumental",
                coding=Coding(display="УЗИ"),
                effective_at=date(2026, 1, 25),
            ),
            DiagnosticReport(
                id="raw-date",
                source=SOURCE,
                category="instrumental",
                coding=Coding(display="Холтер"),
                effective_at_text="весна 2025",
                conclusion="Редкие наджелудочковые экстрасистолы",
            ),
        ]
    )

    context = build_summary_context(record, DashboardService().build(record))

    assert [fact.source_id for fact in context.facts] == [
        "report:ecg",
        "report:echo",
        "report:raw-date",
    ]
    assert context.facts[0].occurred_at == "2026-01-10"
    assert context.facts[0].text == (
        "исследование: ЭКГ; заключение: Синусовый ритм"
    )
    assert context.facts[-1].occurred_at == "весна 2025"


def test_empty_encounters_do_not_displace_encounters_with_text() -> None:
    empty_encounters = [
        Encounter(
            id=f"empty-{index}",
            source=SOURCE,
            occurred_at=date(2026, 1, index + 1),
        )
        for index in range(12)
    ]
    narrative = Encounter(
        id="narrative",
        source=SOURCE,
        occurred_at=date(2025, 12, 1),
        complaints="Сохраняется кашель",
    )
    record = _record(encounters=[narrative, *empty_encounters])

    context = build_summary_context(record, DashboardService().build(record))

    assert [fact.source_id for fact in context.facts] == ["encounter:narrative"]
    assert context.omitted_records == 0


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


def test_context_keeps_the_total_character_limit() -> None:
    record = _record(
        encounters=[
            Encounter(
                id="large",
                source=SOURCE,
                occurred_at=date(2026, 1, 2),
                complaints="x" * 60,
            ),
            Encounter(
                id="s",
                source=SOURCE,
                occurred_at=date(2026, 1, 1),
                complaints="ok",
            ),
        ]
    )

    context = build_summary_context(
        record,
        DashboardService().build(record),
        limits=ContextLimits(total_characters=40),
    )

    assert [fact.source_id for fact in context.facts] == ["encounter:s"]
    assert context.omitted_records == 1


def test_context_does_not_send_chart_metrics_or_raw_observations() -> None:
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
    dashboard = DashboardService().build(record)

    context = build_summary_context(record, dashboard)

    assert dashboard.metrics
    assert context.facts == []
    assert context.source_ids == set()


def test_context_does_not_send_calculated_metrics() -> None:
    record = _record()
    dashboard = DashboardResponse(
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        patient=DashboardPatient(id="patient-1", full_name="Synthetic Patient"),
        metrics=[
            MetricSeries(
                code="egfr-ckd-epi-2021",
                display="Расчётная СКФ",
                unit="mL/min/1.73m2",
                points=[
                    MetricPoint(
                        observed_at=date(2025, 12, 1),
                        value=55.2,
                        source_category="calculated",
                        source_ids=["creatinine-1"],
                        interpretation="G3a",
                    )
                ],
                calculation=CalculationInfo(
                    code="egfr-ckd-epi-2021",
                    description="Расчётная функция почек.",
                    inputs=["Креатинин", "Возраст", "Пол"],
                    purpose="Показать динамику.",
                    method="2021 CKD-EPI creatinine equation",
                    standard="KDIGO 2024",
                ),
            )
        ],
    )

    context = build_summary_context(record, dashboard)

    assert context.facts == []
