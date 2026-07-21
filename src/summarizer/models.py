"""Typed inputs and outputs for the summarization boundary."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from src.contracts.patient.v1.common import ContractModel


FactKind = Literal[
    "allergy",
    "condition",
    "medication",
    "encounter",
    "diagnostic_report",
    "metric",
]


class ContextFact(ContractModel):
    """One traceable fact supplied to the language model."""

    source_id: str = Field(min_length=1)
    kind: FactKind
    occurred_at: str | None = None
    text: str = Field(min_length=1)
    visible_on_dashboard: bool = False


class SummaryContext(ContractModel):
    """Bounded, JSON-serializable context sent to a summarizer client."""

    facts: list[ContextFact] = Field(default_factory=list)
    omitted_records: int = Field(default=0, ge=0)
    truncated_fields: int = Field(default=0, ge=0)

    @property
    def source_ids(self) -> set[str]:
        return {fact.source_id for fact in self.facts}


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
