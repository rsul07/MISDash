"""Application service for validated, traceable summaries."""

from __future__ import annotations

from src.contracts.dashboard.v1 import DashboardResponse
from src.contracts.patient.v1 import PatientRecord
from src.contracts.summarizer.v1 import ClinicalSummary, SummaryItem

from .client import SummaryClient
from .context import ContextLimits, build_summary_context
from .errors import InsufficientClinicalDataError, InvalidSummaryError
from .models import SummaryContext


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
    facts_by_id = {fact.source_id: fact for fact in context.facts}

    def valid(items: list[SummaryItem]) -> list[SummaryItem]:
        result: list[SummaryItem] = []
        for item in items:
            facts = [facts_by_id.get(source_id) for source_id in item.source_ids]
            if not facts or any(fact is None for fact in facts):
                continue
            if all(fact.visible_on_dashboard for fact in facts if fact is not None):
                continue
            result.append(item)
        return result

    return ClinicalSummary(
        symptom_trajectory=valid(summary.symptom_trajectory),
        textual_findings=valid(summary.textual_findings),
        open_loops=valid(summary.open_loops),
    )


def _has_items(summary: ClinicalSummary) -> bool:
    return any(
        (
            summary.symptom_trajectory,
            summary.textual_findings,
            summary.open_loops,
        )
    )
