"""Tests for compact backend-provided insight sections."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.app.components import insights as component
from src.contracts.dashboard.v1 import (
    DashboardPatient,
    DashboardResponse,
    RedFlag,
)


def test_red_flags_render_short_cards_and_expand_rationale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    cards = [MagicMock() for _ in range(3)]
    for card in cards:
        card.expander.return_value = nullcontext()
    columns = [MagicMock(), MagicMock()]
    columns[0].container.side_effect = [cards[0], cards[2]]
    columns[1].container.return_value = cards[1]
    streamlit.columns.return_value = columns
    monkeypatch.setattr(component, "st", streamlit)
    section_header = MagicMock()
    monkeypatch.setattr(component, "render_section_header", section_header)
    dashboard = _dashboard(
        red_flags=[
            RedFlag(
                code="high-risk",
                severity="critical",
                title="Высокий риск",
                explanation="Значение превышает порог. Требуется проверка.",
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
        ]
    )

    component.render_red_flags(dashboard)

    section_header.assert_called_once_with("Красные флаги")
    assert "Высокий риск" in cards[0].markdown.call_args.args[0]
    assert "Срочно" in cards[0].markdown.call_args.args[0]
    assert "Проверить показатель" in cards[1].markdown.call_args.args[0]
    assert "Красный флаг" in cards[1].markdown.call_args.args[0]
    assert "Требует внимания" not in cards[1].markdown.call_args.args[0]
    assert "Справка" in cards[2].markdown.call_args.args[0]
    cards[0].expander.assert_called_once_with("Почему сработало правило")
    streamlit.write.assert_called_once_with("Требуется проверка.")
    streamlit.error.assert_not_called()
    streamlit.warning.assert_not_called()


def test_red_flags_show_quiet_empty_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)
    monkeypatch.setattr(component, "render_section_header", MagicMock())

    component.render_red_flags(_dashboard())

    html = streamlit.markdown.call_args.args[0]
    assert "Активных сигналов нет" in html
    streamlit.columns.assert_not_called()


def test_ai_summary_uses_card_or_clear_empty_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    streamlit.container.return_value = nullcontext()
    monkeypatch.setattr(component, "st", streamlit)
    monkeypatch.setattr(component, "render_section_header", MagicMock())

    component.render_ai_summary(_dashboard(ai_summary="Состояние стабильное."))
    component.render_ai_summary(_dashboard())

    streamlit.write.assert_called_once_with("Состояние стабильное.")
    assert "Сводка ещё не сформирована" in streamlit.markdown.call_args.args[0]


def test_explanation_split_respects_decimal_values() -> None:
    summary, details = component._split_explanation(
        "Последнее значение 8.64% от 19.05.2026. Цель индивидуальна."
    )

    assert summary == "Последнее значение 8.64% от 19.05.2026."
    assert details == "Цель индивидуальна."


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
