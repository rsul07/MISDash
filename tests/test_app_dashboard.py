"""Tests for top-level lazy dashboard navigation."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.app import dashboard as component
from src.contracts.dashboard.v1 import DashboardPatient, DashboardResponse
from src.contracts.patient.v1 import Patient, PatientRecord
from src.contracts.patient.v1.common import SourceReference


SOURCE = SourceReference(block="test")


@pytest.mark.parametrize(
    ("selected", "expected"),
    [
        (component.OVERVIEW, ("patient", "flags", "context")),
        (component.METRICS, ("metrics",)),
        (component.VISITS, ("visits",)),
    ],
)
def test_navigation_renders_only_selected_section(
    monkeypatch: pytest.MonkeyPatch,
    selected: str,
    expected: tuple[str, ...],
) -> None:
    streamlit = MagicMock()
    streamlit.segmented_control.return_value = selected
    monkeypatch.setattr(component, "st", streamlit)
    renderers = _renderer_mocks(monkeypatch)

    component.render_dashboard(b"{}", _record(), _dashboard())

    called = tuple(name for name, renderer in renderers.items() if renderer.called)
    assert called == expected
    streamlit.segmented_control.assert_called_once_with(
        "Раздел дашборда",
        component.SECTIONS,
        default=component.OVERVIEW,
        key="dashboard-section",
        label_visibility="collapsed",
        width="stretch",
    )


def test_summary_section_keeps_generation_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    streamlit.segmented_control.return_value = component.SUMMARY
    monkeypatch.setattr(component, "st", streamlit)
    renderers = _renderer_mocks(monkeypatch)
    generated = _dashboard(ai_summary="Готовая сводка")
    renderers["controls"].return_value = generated

    component.render_dashboard(b"file", _record(), _dashboard())

    renderers["controls"].assert_called_once()
    renderers["summary"].assert_called_once_with(generated)
    for name in ("patient", "flags", "context", "metrics", "visits"):
        renderers[name].assert_not_called()


def test_missing_selection_falls_back_to_overview(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    streamlit.segmented_control.return_value = None
    monkeypatch.setattr(component, "st", streamlit)
    renderers = _renderer_mocks(monkeypatch)

    component.render_dashboard(b"{}", _record(), _dashboard())

    renderers["patient"].assert_called_once()
    renderers["flags"].assert_called_once()
    renderers["context"].assert_called_once()


def _renderer_mocks(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    names = {
        "patient": "render_patient_card",
        "flags": "render_red_flags",
        "context": "render_patient_context",
        "metrics": "render_metrics",
        "visits": "render_visits",
        "controls": "render_summary_controls",
        "summary": "render_ai_summary",
    }
    result: dict[str, MagicMock] = {}
    for key, attribute in names.items():
        renderer = MagicMock()
        monkeypatch.setattr(component, attribute, renderer)
        result[key] = renderer
    return result


def _record() -> PatientRecord:
    return PatientRecord(
        patient=Patient(id="patient-1", full_name="Пациент", source=SOURCE)
    )


def _dashboard(*, ai_summary: str | None = None) -> DashboardResponse:
    return DashboardResponse(
        generated_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        patient=DashboardPatient(id="patient-1", full_name="Пациент"),
        ai_summary=ai_summary,
    )
