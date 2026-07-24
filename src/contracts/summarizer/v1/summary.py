"""Structured output contract for traceable clinical summaries."""

from __future__ import annotations

from pydantic import Field

from src.contracts.patient.v1.common import ContractModel


class SummaryItem(ContractModel):
    """A concise clinical statement backed by context source identifiers."""

    text: str = Field(min_length=1, max_length=400)
    source_ids: list[str] = Field(min_length=1, max_length=3)


class ClinicalSummary(ContractModel):
    """Narrative clinical insights grounded in unstructured source text."""

    symptom_trajectory: list[SummaryItem] = Field(
        default_factory=list,
        max_length=3,
        description="Dated evolution of symptoms documented in clinical text.",
    )
    textual_findings: list[SummaryItem] = Field(
        default_factory=list,
        max_length=3,
        description="Important clinical and instrumental findings from source text.",
    )
    open_loops: list[SummaryItem] = Field(
        default_factory=list,
        max_length=3,
        description="Explicitly unfinished plans, pending actions, or follow-up questions.",
    )
