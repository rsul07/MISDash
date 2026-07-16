"""Tests for provider isolation and source validation."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.backend import DashboardService
from src.contracts.patient.v1 import Condition, Patient, PatientRecord
from src.contracts.patient.v1.common import Coding, SourceReference
from src.summarizer import (
    ClinicalSummary,
    GeminiSummaryClient,
    InsufficientClinicalDataError,
    InvalidSummaryError,
    MissingApiKeyError,
    SummaryContext,
    SummaryItem,
    SummaryService,
    SummarySettings,
    format_summary,
)


SOURCE = SourceReference(block="test")


class FakeSummaryClient:
    def __init__(self, result: ClinicalSummary) -> None:
        self.result = result
        self.calls = 0

    def generate(self, context: SummaryContext) -> ClinicalSummary:
        self.calls += 1
        return self.result


def _record(*, with_condition: bool = True) -> PatientRecord:
    conditions = []
    if with_condition:
        conditions.append(
            Condition(
                id="condition-1",
                source=SOURCE,
                coding=Coding(code="I10", display="Гипертензия"),
            )
        )
    return PatientRecord(
        patient=Patient(id="patient-1", full_name="Synthetic", source=SOURCE),
        conditions=conditions,
    )


def _dashboard(record: PatientRecord):
    return DashboardService().build(
        record,
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_service_keeps_only_items_with_known_sources() -> None:
    client = FakeSummaryClient(
        ClinicalSummary(
            diagnoses=[
                SummaryItem(
                    text="Артериальная гипертензия.",
                    source_ids=["condition:0"],
                ),
                SummaryItem(text="Выдуманный диагноз.", source_ids=["missing:1"]),
            ]
        )
    )
    record = _record()

    summary = SummaryService(client).summarize(record, _dashboard(record))

    assert [item.text for item in summary.diagnoses] == [
        "Артериальная гипертензия."
    ]
    assert client.calls == 1


def test_service_does_not_call_provider_for_empty_context() -> None:
    client = FakeSummaryClient(ClinicalSummary())
    record = _record(with_condition=False)

    with pytest.raises(InsufficientClinicalDataError, match="Недостаточно"):
        SummaryService(client).summarize(record, _dashboard(record))

    assert client.calls == 0


def test_service_rejects_response_without_traceable_items() -> None:
    client = FakeSummaryClient(
        ClinicalSummary(
            diagnoses=[SummaryItem(text="Нет источника", source_ids=["missing:1"])]
        )
    )
    record = _record()

    with pytest.raises(InvalidSummaryError, match="проверяемым источником"):
        SummaryService(client).summarize(record, _dashboard(record))


def test_gemini_client_requests_structured_output_and_parses_it() -> None:
    output = ClinicalSummary(
        diagnoses=[SummaryItem(text="Гипертензия", source_ids=["condition:0"])]
    )
    calls: list[dict[str, object]] = []

    class Interactions:
        def create(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(output_text=output.model_dump_json())

    sdk_client = SimpleNamespace(interactions=Interactions())
    client = GeminiSummaryClient(model="gemini-test", sdk_client=sdk_client)

    result = client.generate(
        SummaryContext(
            facts=[
                {
                    "source_id": "condition:0",
                    "kind": "condition",
                    "text": "диагноз: Гипертензия",
                }
            ]
        )
    )

    assert result == output
    assert calls[0]["model"] == "gemini-test"
    assert calls[0]["store"] is False
    response_format = calls[0]["response_format"]
    assert isinstance(response_format, dict)
    assert response_format["mime_type"] == "application/json"
    assert "patient_context" in str(calls[0]["input"])


def test_gemini_client_rejects_invalid_json() -> None:
    sdk_client = SimpleNamespace(
        interactions=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(output_text="not-json")
        )
    )

    with pytest.raises(InvalidSummaryError, match="контракту"):
        GeminiSummaryClient(model="gemini-test", sdk_client=sdk_client).generate(
            SummaryContext()
        )


def test_missing_key_is_reported_before_sdk_initialization() -> None:
    with pytest.raises(MissingApiKeyError, match="GEMINI_API_KEY"):
        GeminiSummaryClient.from_settings(SummarySettings(api_key=None))


def test_formatter_preserves_contract_sections() -> None:
    markdown = format_summary(
        ClinicalSummary(
            diagnoses=[SummaryItem(text="Гипертензия", source_ids=["condition:0"])],
            next_visit_priorities=[
                SummaryItem(text="Уточнить терапию", source_ids=["condition:0"])
            ],
        )
    )

    assert "### Диагнозы\n\n- Гипертензия" in markdown
    assert "### Важно на ближайшем приёме\n\n- Уточнить терапию" in markdown
    assert "condition:0" not in markdown
