"""Tests for provider isolation and source validation."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.backend import DashboardService
from src.contracts.patient.v1 import Condition, Encounter, Patient, PatientRecord
from src.contracts.patient.v1.common import Coding, SourceReference
from src.summarizer import (
    ClinicalSummary,
    DEFAULT_GEMINI_MODEL,
    GeminiSummaryClient,
    InsufficientClinicalDataError,
    InvalidSummaryError,
    MissingApiKeyError,
    SummaryContext,
    SummaryItem,
    SummaryProviderError,
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


def _record(
    *,
    with_condition: bool = True,
    with_encounter: bool = False,
) -> PatientRecord:
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
        encounters=(
            [
                Encounter(
                    id="visit-1",
                    source=SOURCE,
                    complaints="Утомляемость",
                )
            ]
            if with_encounter
            else []
        ),
    )


def _dashboard(record: PatientRecord):
    return DashboardService().build(
        record,
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_service_keeps_only_new_items_with_known_sources() -> None:
    client = FakeSummaryClient(
        ClinicalSummary(
            textual_findings=[
                SummaryItem(
                    text="На последнем приёме отмечена утомляемость.",
                    source_ids=["encounter:visit-1"],
                ),
                SummaryItem(
                    text="Артериальная гипертензия.",
                    source_ids=["condition:0"],
                ),
                SummaryItem(text="Выдуманная находка.", source_ids=["missing:1"]),
            ]
        )
    )
    record = _record(with_encounter=True)

    summary = SummaryService(client).summarize(record, _dashboard(record))

    assert [item.text for item in summary.textual_findings] == [
        "На последнем приёме отмечена утомляемость."
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
            textual_findings=[
                SummaryItem(text="Нет источника", source_ids=["missing:1"])
            ]
        )
    )
    record = _record()

    with pytest.raises(InvalidSummaryError, match="проверяемым источником"):
        SummaryService(client).summarize(record, _dashboard(record))


def test_gemini_client_requests_structured_output_and_parses_it() -> None:
    output = ClinicalSummary(
        textual_findings=[
            SummaryItem(text="Находка", source_ids=["report:report-1"])
        ]
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
                    "source_id": "report:report-1",
                    "kind": "diagnostic_report",
                    "text": "исследование: ЭКГ; заключение: Синусовый ритм",
                }
            ]
        )
    )

    assert result == output
    assert calls[0]["model"] == "gemini-test"
    assert calls[0]["store"] is False
    response_format = calls[0]["response_format"]
    assert isinstance(response_format, dict)
    assert response_format == {
        "type": "text",
        "mime_type": "application/json",
        "schema": ClinicalSummary.model_json_schema(),
    }
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


def test_summary_limits_each_section_to_three_items() -> None:
    items = [
        SummaryItem(text=f"Симптом {index}", source_ids=[f"encounter:{index}"])
        for index in range(4)
    ]

    with pytest.raises(ValidationError):
        ClinicalSummary(symptom_trajectory=items)


def test_missing_key_is_reported_before_sdk_initialization() -> None:
    with pytest.raises(MissingApiKeyError, match="GEMINI_API_KEY"):
        GeminiSummaryClient.from_settings(SummarySettings(api_key=None))


def test_current_default_model_is_used() -> None:
    assert DEFAULT_GEMINI_MODEL == "gemini-3.5-flash"


@pytest.mark.parametrize(
    ("status_code", "message"),
    (
        (404, "GEMINI_MODEL"),
        (401, "API-ключ"),
        (429, "квота"),
    ),
)
def test_gemini_client_explains_provider_errors(
    status_code: int,
    message: str,
) -> None:
    class ProviderFailure(Exception):
        def __init__(self) -> None:
            super().__init__("provider failure")
            self.status_code = status_code

    def fail(**kwargs):
        raise ProviderFailure()

    sdk_client = SimpleNamespace(interactions=SimpleNamespace(create=fail))

    with pytest.raises(SummaryProviderError, match=message):
        GeminiSummaryClient(model="gemini-test", sdk_client=sdk_client).generate(
            SummaryContext()
        )


def test_formatter_preserves_contract_sections() -> None:
    markdown = format_summary(
        ClinicalSummary(
            symptom_trajectory=[
                SummaryItem(
                    text="Головная боль стала реже",
                    source_ids=["encounter:1", "encounter:2"],
                )
            ],
            open_loops=[
                SummaryItem(
                    text="В плане от 2026-01-01 указана повторная консультация",
                    source_ids=["encounter:1"],
                )
            ],
        )
    )

    assert "### Динамика симптомов\n\n- Головная боль стала реже" in markdown
    assert "### Незавершённые планы и вопросы" in markdown
    assert "condition:0" not in markdown
