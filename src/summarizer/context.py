"""Deterministic and bounded context projection for LLM summarization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from src.contracts.dashboard.v1 import DashboardResponse
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
        occurred_at: date | datetime | str | None = None,
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

    encounters = sorted(
        (encounter for encounter in record.encounters if _has_encounter_text(encounter)),
        key=_encounter_key,
        reverse=True,
    )
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

    return builder.result()


def _add_encounter(builder: _ContextBuilder, encounter: Encounter) -> None:
    follow_up = encounter.follow_up_at or encounter.follow_up_at_text
    builder.add(
        f"encounter:{encounter.id}",
        "encounter",
        (
            ("жалобы", encounter.complaints),
            ("анамнез", encounter.history),
            ("объективный статус", encounter.objective),
            ("план", encounter.plan),
            ("повторный приём", follow_up),
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
        occurred_at=_report_date(report),
    )


def _has_encounter_text(encounter: Encounter) -> bool:
    return any(
        (
            encounter.complaints,
            encounter.history,
            encounter.objective,
            encounter.plan,
            encounter.follow_up_at,
            encounter.follow_up_at_text,
        )
    )


def _encounter_key(encounter: Encounter) -> tuple[str, str]:
    return (_date_key(encounter.occurred_at), encounter.id)


def _report_key(report: DiagnosticReport) -> tuple[bool, str, str]:
    parsed_date = report.effective_at or report.issued_at
    return (
        parsed_date is not None,
        _date_key(parsed_date) if parsed_date is not None else report.effective_at_text or "",
        report.id,
    )


def _report_date(report: DiagnosticReport) -> date | datetime | str | None:
    return report.effective_at or report.issued_at or report.effective_at_text


def _date_key(value: date | datetime | None) -> str:
    return _iso_date(value) or ""


def _iso_date(value: date | datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()
