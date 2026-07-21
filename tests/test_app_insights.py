"""Tests for backend-provided insight sections."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.app.components import insights as component
from src.contracts.dashboard.v1 import (
    DashboardPatient,
    DashboardResponse,
    RedFlag,
)


def test_insights_render_backend_values(monkeypatch: pytest.MonkeyPatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)
    dashboard = _dashboard(
        red_flags=[
            RedFlag(
                code="high-risk",
                severity="critical",
                title="Высокий риск",
                explanation="Требуется внимание",
            ),
            RedFlag(
                code="check",
                severity="warning",
                title="Проверить показатель",
                explanation="Нужен контроль",
            ),
            RedFlag(
                code="note",
                severity="info",
                title="Справка",
                explanation="Дополнительная информация",
            ),
        ],
        ai_summary="Состояние стабильное.",
    )

    component.render_insights(dashboard)

    streamlit.error.assert_called_once_with("Высокий риск — Требуется внимание")
    streamlit.warning.assert_called_once_with("Проверить показатель — Нужен контроль")
    streamlit.info.assert_called_once_with("Справка — Дополнительная информация")
    streamlit.write.assert_called_once_with("Состояние стабильное.")


def test_insights_show_neutral_empty_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)

    component.render_insights(_dashboard())

    assert [call.args[0] for call in streamlit.info.call_args_list] == [
        "Пока нет данных",
        "Пока нет данных",
    ]
    streamlit.error.assert_not_called()
    streamlit.warning.assert_not_called()
    streamlit.write.assert_not_called()


def _dashboard(
    *,
    red_flags: list[RedFlag] | None = None,
    ai_summary: str | None = None,
) -> DashboardResponse:
    return DashboardResponse(
        generated_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        patient=DashboardPatient(id="patient-1", full_name="Пациент"),
        red_flags=red_flags or [],
        ai_summary=ai_summary,
    )
