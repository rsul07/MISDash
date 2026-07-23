"""Tests for on-demand Streamlit summary orchestration."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.app import summary as component
from src.backend import DashboardService
from src.contracts.patient.v1 import Condition, Patient, PatientRecord
from src.contracts.patient.v1.common import Coding, SourceReference
from src.summarizer import (
    ClinicalSummary,
    SummaryItem,
    SummarySettings,
)


SOURCE = SourceReference(block="test")


class FakeService:
    def __init__(self) -> None:
        self.calls = 0

    def summarize(self, record, dashboard) -> ClinicalSummary:
        self.calls += 1
        return ClinicalSummary(
            textual_findings=[
                SummaryItem(text="Важная находка", source_ids=["encounter:1"])
            ]
        )


def _record():
    return PatientRecord(
        patient=Patient(id="patient-1", full_name="Synthetic", source=SOURCE),
        conditions=[
            Condition(
                id="condition-1",
                source=SOURCE,
                coding=Coding(code="I10", display="Гипертензия"),
            )
        ],
    )


def _dashboard(record):
    return DashboardService().build(
        record,
        generated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _streamlit(*button_results: bool) -> MagicMock:
    streamlit = MagicMock()
    streamlit.session_state = {}
    streamlit.button.side_effect = button_results
    streamlit.spinner.return_value = nullcontext()
    return streamlit


def test_summary_is_generated_once_and_survives_rerun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(True, False)
    monkeypatch.setattr(component, "st", streamlit)
    service = FakeService()
    settings = SummarySettings(api_key="test-key", model="gemini-test")
    record = _record()
    dashboard = _dashboard(record)

    first = component.render_summary_controls(
        b"same-file",
        record,
        dashboard,
        settings=settings,
        service=service,
    )
    second = component.render_summary_controls(
        b"same-file",
        record,
        dashboard,
        settings=settings,
        service=service,
    )

    assert service.calls == 1
    assert first.ai_summary == "### Текстовые находки\n\n- Важная находка"
    assert second.ai_summary == first.ai_summary
    assert streamlit.button.call_args_list[1].args[0] == "Сформировать заново"


def test_changing_file_clears_previous_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(True, False)
    monkeypatch.setattr(component, "st", streamlit)
    service = FakeService()
    settings = SummarySettings(api_key="test-key")
    record = _record()
    dashboard = _dashboard(record)

    component.render_summary_controls(
        b"first-file", record, dashboard, settings=settings, service=service
    )
    changed = component.render_summary_controls(
        b"second-file", record, dashboard, settings=settings, service=service
    )

    assert changed.ai_summary is None
    assert service.calls == 1


def test_missing_key_disables_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(False)
    monkeypatch.setattr(component, "st", streamlit)
    record = _record()

    result = component.render_summary_controls(
        b"file",
        record,
        _dashboard(record),
        settings=SummarySettings(api_key=None),
    )

    assert result.ai_summary is None
    assert streamlit.button.call_args.kwargs["disabled"] is True
    streamlit.warning.assert_called_once_with(
        "Для генерации сводки добавьте GEMINI_API_KEY в локальный файл .env."
    )
