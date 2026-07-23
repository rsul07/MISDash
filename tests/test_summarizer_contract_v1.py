"""Executable specification for the ClinicalSummary v1 contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.contracts.summarizer.v1 import ClinicalSummary, SummaryItem


def test_clinical_summary_serializes_traceable_sections() -> None:
    summary = ClinicalSummary(
        recent_changes=[
            SummaryItem(
                text="HbA1c вырос за последний год.",
                source_ids=["metric:hba1c"],
            )
        ]
    )

    payload = summary.model_dump(mode="json")

    assert payload["recent_changes"][0] == {
        "text": "HbA1c вырос за последний год.",
        "source_ids": ["metric:hba1c"],
    }
    assert payload["important_findings"] == []


def test_clinical_summary_rejects_untraceable_item() -> None:
    with pytest.raises(ValidationError):
        SummaryItem(text="Нет источника.", source_ids=[])
