"""Executable specification for the ClinicalSummary v1 contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.contracts.summarizer.v1 import ClinicalSummary, SummaryItem


def test_clinical_summary_serializes_traceable_sections() -> None:
    summary = ClinicalSummary(
        symptom_trajectory=[
            SummaryItem(
                text="К 2026-01-15 головная боль стала реже.",
                source_ids=["encounter:visit-2", "encounter:visit-1"],
            )
        ]
    )

    payload = summary.model_dump(mode="json")

    assert set(payload) == {
        "symptom_trajectory",
        "compliance_and_behavior",
        "textual_findings",
        "open_loops",
    }
    assert payload["symptom_trajectory"][0] == {
        "text": "К 2026-01-15 головная боль стала реже.",
        "source_ids": ["encounter:visit-2", "encounter:visit-1"],
    }
    assert payload["compliance_and_behavior"] == []
    assert payload["textual_findings"] == []
    assert payload["open_loops"] == []


def test_clinical_summary_rejects_untraceable_item() -> None:
    with pytest.raises(ValidationError):
        SummaryItem(text="Нет источника.", source_ids=[])
