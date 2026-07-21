"""Tests for the visit table component."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.app.components import visits as component
from src.contracts.dashboard.v1 import (
    CodeLabel,
    DashboardPatient,
    DashboardResponse,
    VisitSummary,
)


def test_visits_preserve_backend_order_and_show_required_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)
    dashboard = _dashboard(
        VisitSummary(
            id="new",
            occurred_at=datetime(2026, 7, 14, 10, 30),
            practitioner="Петров П.П.",
            specialty="Терапевт",
            diagnoses=[CodeLabel(code="I10", display="Гипертензия")],
            complaints="Головная боль",
        ),
        VisitSummary(
            id="old",
            occurred_at=date(2025, 1, 2),
            diagnoses=[CodeLabel(display="Профилактический осмотр")],
        ),
    )

    component.render_visits(dashboard)

    rows = streamlit.dataframe.call_args.args[0]
    assert rows == [
        {
            "Дата": "14.07.2026 10:30",
            "Врач": "Петров П.П.",
            "Специальность": "Терапевт",
            "Основной диагноз": "I10 — Гипертензия",
            "Жалобы": "Головная боль",
        },
        {
            "Дата": "02.01.2025",
            "Врач": "Нет данных",
            "Специальность": "Нет данных",
            "Основной диагноз": "Профилактический осмотр",
            "Жалобы": "Нет данных",
        },
    ]
    assert streamlit.dataframe.call_args.kwargs == {
        "hide_index": True,
        "use_container_width": True,
    }


def test_visits_show_empty_state(monkeypatch: pytest.MonkeyPatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)

    component.render_visits(_dashboard())

    streamlit.info.assert_called_once_with("Пока нет данных")
    streamlit.dataframe.assert_not_called()


def _dashboard(*visits: VisitSummary) -> DashboardResponse:
    return DashboardResponse(
        generated_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        patient=DashboardPatient(id="patient-1", full_name="Пациент"),
        visits=list(visits),
    )
