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

    text: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)


class ClinicalSummary(ContractModel):
    """Structured result required by the dashboard and technical assignment."""

    diagnoses: list[SummaryItem] = Field(default_factory=list)
    therapy: list[SummaryItem] = Field(default_factory=list)
    dynamics: list[SummaryItem] = Field(default_factory=list)
    next_visit_priorities: list[SummaryItem] = Field(default_factory=list)
