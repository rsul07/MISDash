"""Application service for validated, traceable summaries."""

from __future__ import annotations

from src.contracts.dashboard.v1 import DashboardResponse
from src.contracts.patient.v1 import PatientRecord

from .client import SummaryClient
from .context import ContextLimits, build_summary_context
from .errors import InsufficientClinicalDataError, InvalidSummaryError
from .models import ClinicalSummary, SummaryContext, SummaryItem


class SummaryService:
    def __init__(
        self,
        client: SummaryClient,
        *,
        limits: ContextLimits | None = None,
    ) -> None:
        self.client = client
        self.limits = limits

    def summarize(
        self,
        record: PatientRecord,
        dashboard: DashboardResponse,
    ) -> ClinicalSummary:
        context = build_summary_context(record, dashboard, limits=self.limits)
        if not context.facts:
            raise InsufficientClinicalDataError(
                "Недостаточно клинических данных для формирования ИИ-сводки."
            )
        summary = self.client.generate(context)
        validated = _keep_traceable_items(summary, context)
        if not _has_items(validated):
            raise InvalidSummaryError(
                "Gemini не вернул ни одного пункта с проверяемым источником."
            )
        return validated


def _keep_traceable_items(
    summary: ClinicalSummary,
    context: SummaryContext,
) -> ClinicalSummary:
    source_ids = context.source_ids

    def valid(items: list[SummaryItem]) -> list[SummaryItem]:
        return [
            item
            for item in items
            if item.source_ids and set(item.source_ids).issubset(source_ids)
        ]

    return ClinicalSummary(
        diagnoses=valid(summary.diagnoses),
        therapy=valid(summary.therapy),
        dynamics=valid(summary.dynamics),
        next_visit_priorities=valid(summary.next_visit_priorities),
    )


def _has_items(summary: ClinicalSummary) -> bool:
    return any(
        (
            summary.diagnoses,
            summary.therapy,
            summary.dynamics,
            summary.next_visit_priorities,
        )
    )
