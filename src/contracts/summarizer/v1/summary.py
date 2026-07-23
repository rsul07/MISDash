"""Structured output contract for traceable clinical summaries."""

from __future__ import annotations

from pydantic import Field

from src.contracts.patient.v1.common import ContractModel


class SummaryItem(ContractModel):
    """A concise clinical statement backed by context source identifiers."""

    text: str = Field(min_length=1, max_length=400)
    source_ids: list[str] = Field(min_length=1, max_length=3)


class ClinicalSummary(ContractModel):
    """Non-duplicating insights that add information to the dashboard."""

    recent_changes: list[SummaryItem] = Field(
        default_factory=list,
        max_length=3,
        description="Dated clinical or metric changes, not static diagnoses.",
    )
    important_findings: list[SummaryItem] = Field(
        default_factory=list,
        max_length=3,
        description="Important free-text findings not already visible on the dashboard.",
    )
    unresolved_issues: list[SummaryItem] = Field(
        default_factory=list,
        max_length=3,
        description="Explicitly documented unresolved issues or follow-up needs.",
    )
    next_visit_focus: list[SummaryItem] = Field(
        default_factory=list,
        max_length=3,
        description="Dated plan items to verify at the next visit, not new advice.",
    )
