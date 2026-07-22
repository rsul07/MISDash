"""Deterministic and bounded context projection for LLM summarization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable

from src.contracts.dashboard.v1 import DashboardResponse, MetricSeries
from src.contracts.patient.v1 import DiagnosticReport, Encounter, PatientRecord

from .models import ContextFact, FactKind, SummaryContext


@dataclass(frozen=True)
class ContextLimits:
    """Limits that keep a patient export from becoming an unbounded prompt."""

    encounters: int = 12
    diagnostic_reports: int = 10
    field_characters: int = 2_000
    total_characters: int = 50_000


class _ContextBuilder:
    def __init__(self, limits: ContextLimits) -> None:
        self.limits = limits
        self.facts: list[ContextFact] = []
        self.omitted_records = 0
        self.truncated_fields = 0
        self._used_characters = 0

    def clean(self, value: object) -> str | None:
        if value is None:
            return None
        text = " ".join(str(value).split())
        if not text:
            return None
        if len(text) <= self.limits.field_characters:
            return text
        self.truncated_fields += 1
        return f"{text[: self.limits.field_characters - 1].rstrip()}…"

    def add(
        self,
        source_id: str,
        kind: FactKind,
        parts: Iterable[tuple[str, object]],
        *,
        occurred_at: date | datetime | None = None,
        visible_on_dashboard: bool = False,
    ) -> None:
        text_parts: list[str] = []
        for label, value in parts:
            cleaned = self.clean(value)
            if cleaned is not None:
                text_parts.append(f"{label}: {cleaned}")
        if not text_parts:
            return
        fact = ContextFact(
            source_id=source_id,
            kind=kind,
            occurred_at=_iso_date(occurred_at),
            text="; ".join(text_parts),
            visible_on_dashboard=visible_on_dashboard,
        )
        fact_size = len(fact.source_id) + len(fact.text) + len(fact.occurred_at or "")
        if self._used_characters + fact_size > self.limits.total_characters:
            self.omitted_records += 1
            return
        self.facts.append(fact)
        self._used_characters += fact_size

    def result(self) -> SummaryContext:
        return SummaryContext(
            facts=self.facts,
            omitted_records=self.omitted_records,
            truncated_fields=self.truncated_fields,
        )


def build_summary_context(
    record: PatientRecord,
    dashboard: DashboardResponse,
    *,
    limits: ContextLimits | None = None,
) -> SummaryContext:
    """Project canonical data into compact facts without exposing raw observations."""

    limits = limits or ContextLimits()
    builder = _ContextBuilder(limits)

    for index, allergy in enumerate(dashboard.allergies):
        builder.add(
            f"allergy:{index}",
            "allergy",
            (("аллерген", allergy.agent), ("реакция", allergy.reaction)),
            visible_on_dashboard=True,
        )

    for index, condition in enumerate(dashboard.conditions):
        builder.add(
            f"condition:{index}",
            "condition",
            (
                ("диагноз", condition.display),
                ("код", condition.code),
                ("стадия", condition.stage),
                ("статус", condition.clinical_status),
            ),
            visible_on_dashboard=True,
        )

    for index, medication in enumerate(dashboard.current_medications):
        builder.add(
            f"medication:{index}",
            "medication",
            (
                ("препарат", medication.name),
                ("доза", medication.dose),
                ("частота", medication.frequency),
                ("форма", medication.form),
            ),
            visible_on_dashboard=True,
        )

    encounters = sorted(record.encounters, key=_encounter_key, reverse=True)
    builder.omitted_records += max(0, len(encounters) - limits.encounters)
    for encounter in encounters[: limits.encounters]:
        _add_encounter(builder, encounter)

    reports = sorted(
        (
            report
            for report in record.diagnostic_reports
            if report.category == "instrumental" and report.conclusion
        ),
        key=_report_key,
        reverse=True,
    )
    builder.omitted_records += max(0, len(reports) - limits.diagnostic_reports)
    for report in reports[: limits.diagnostic_reports]:
        _add_report(builder, report)

    for metric in dashboard.metrics:
        _add_metric(builder, metric)

    return builder.result()


def _add_encounter(builder: _ContextBuilder, encounter: Encounter) -> None:
    diagnoses = ", ".join(
        filter(
            None,
            (
                f"{diagnosis.coding.display} ({diagnosis.coding.code})"
                if diagnosis.coding.code
                else diagnosis.coding.display
                for diagnosis in encounter.diagnoses
            ),
        )
    )
    builder.add(
        f"encounter:{encounter.id}",
        "encounter",
        (
            ("специалист", encounter.practitioner.specialty),
            ("жалобы", encounter.complaints),
            ("анамнез", encounter.history),
            ("объективно", encounter.objective),
            ("диагнозы", diagnoses),
            ("план", encounter.plan),
        ),
        occurred_at=encounter.occurred_at,
    )


def _add_report(builder: _ContextBuilder, report: DiagnosticReport) -> None:
    builder.add(
        f"report:{report.id}",
        "diagnostic_report",
        (
            ("исследование", report.coding.display),
            ("заключение", report.conclusion),
        ),
        occurred_at=report.effective_at or report.issued_at,
    )


def _add_metric(builder: _ContextBuilder, metric: MetricSeries) -> None:
    if not metric.points:
        return
    points = sorted(metric.points, key=lambda item: _date_key(item.observed_at))
    latest = points[-1]
    latest_date = _as_date(latest.observed_at)
    recent_start = latest_date - timedelta(days=365)
    previous_start = latest_date - timedelta(days=730)
    recent = [
        point
        for point in points
        if recent_start < _as_date(point.observed_at) <= latest_date
    ]
    previous = [
        point
        for point in points
        if previous_start < _as_date(point.observed_at) <= recent_start
    ]
    unit = f" {metric.unit}" if metric.unit else ""
    parts: list[tuple[str, object]] = [
        ("показатель", metric.display),
        ("последнее значение", f"{latest.value:g}{unit} от {_iso_date(latest.observed_at)}"),
        ("измерений за последние 12 месяцев", len(recent)),
    ]
    if metric.calculation is not None:
        parts.extend(
            (
                ("тип значения", "рассчитано детерминированным кодом"),
                ("метод расчёта", metric.calculation.method),
            )
        )
    if recent and previous:
        recent_mean = sum(point.value for point in recent) / len(recent)
        previous_mean = sum(point.value for point in previous) / len(previous)
        delta = recent_mean - previous_mean
        parts.extend(
            (
                ("среднее за последние 12 месяцев", f"{recent_mean:.2f}{unit}"),
                ("среднее за предыдущие 12 месяцев", f"{previous_mean:.2f}{unit}"),
                ("изменение средних", f"{delta:+.2f}{unit}"),
                ("измерений в предыдущем периоде", len(previous)),
            )
        )
    else:
        parts.append(("сравнение периодов", "недостаточно данных"))
    builder.add(
        f"metric:{metric.code}",
        "metric",
        parts,
    )


def _encounter_key(encounter: Encounter) -> tuple[str, str]:
    return (_date_key(encounter.occurred_at), encounter.id)


def _report_key(report: DiagnosticReport) -> tuple[str, str]:
    return (_date_key(report.effective_at or report.issued_at), report.id)


def _date_key(value: date | datetime | None) -> str:
    return _iso_date(value) or ""


def _iso_date(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _as_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value
