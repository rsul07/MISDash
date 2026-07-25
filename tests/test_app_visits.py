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


def test_visits_preserve_backend_order_and_show_clinical_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    streamlit.text_input.return_value = ""
    monkeypatch.setattr(component, "st", streamlit)
    monkeypatch.setattr(component, "render_section_header", MagicMock())
    dashboard = _dashboard(
        VisitSummary(
            id="new",
            occurred_at=datetime(2026, 7, 14, 10, 30),
            practitioner="Петров П.П.",
            specialty="Терапевт",
            diagnoses=[
                CodeLabel(code="I10", display="Гипертензия"),
                CodeLabel(code="E11.9", display="Сахарный диабет"),
            ],
            complaints="Головная боль",
        ),
        VisitSummary(
            id="old",
            occurred_at=date(2025, 1, 2),
            diagnoses=[CodeLabel(display="Профилактический осмотр")],
        ),
    )

    component.render_visits(dashboard)

    html = streamlit.markdown.call_args.args[0]
    assert streamlit.markdown.call_args.kwargs["unsafe_allow_html"] is True
    assert 'class="mis-visit-table"' in html
    assert html.index("14.07.2026") < html.index("02.01.2025")
    assert "Петров П.П." in html
    assert "Терапевт" in html
    assert 'data-label="Врач"' in html
    assert 'data-label="Диагнозы"' in html
    assert "I10 — Гипертензия" in html
    assert "основной" in html
    assert 'class="mis-visit-diagnosis-chip"' in html
    assert "E11.9" in html
    assert "Головная боль" in html


def test_visits_show_empty_state(monkeypatch: pytest.MonkeyPatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)
    monkeypatch.setattr(component, "render_section_header", MagicMock())

    component.render_visits(_dashboard())

    streamlit.info.assert_called_once_with("Пока нет данных")
    streamlit.markdown.assert_not_called()


def test_filter_rows_searches_all_visible_fields() -> None:
    rows = [
        {"Дата": "01.01.2026", "Врач": "Иванов", "Жалобы": "Головная боль"},
        {"Дата": "02.01.2026", "Врач": "Петров", "Жалобы": "Нет жалоб"},
    ]

    assert component._filter_rows(rows, "головная") == [rows[0]]
    assert component._filter_rows(rows, " ПЕТРОВ ") == [rows[1]]
    assert component._filter_rows(rows, "") == rows


def test_visit_table_limits_secondary_diagnoses_and_escapes_html() -> None:
    visit = VisitSummary(
        id="visit-1",
        diagnoses=[
            CodeLabel(code="I10", display="<Основной>"),
            CodeLabel(code="E11.9", display="Диабет"),
            CodeLabel(code="N18.3", display="ХБП"),
            CodeLabel(code="E78.2", display="Дислипидемия"),
            CodeLabel(code="I25.2", display='ПИКС "уточнение"'),
            CodeLabel(code="H36.0", display="Ретинопатия"),
        ],
        complaints="<script>alert(1)</script>",
    )

    html = component._visit_table_html([visit])

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;Основной&gt;" in html
    assert html.count('class="mis-visit-diagnosis-chip"') == 4
    assert "mis-visit-diagnosis-more" in html
    assert ">+1</span>" in html
    assert "&quot;уточнение&quot;" in html


def test_visit_search_includes_secondary_diagnoses() -> None:
    visit = VisitSummary(
        id="visit-1",
        diagnoses=[
            CodeLabel(code="I10", display="Гипертензия"),
            CodeLabel(code="E11.9", display="Сахарный диабет"),
        ],
    )
    row = component._visit_row(visit)

    assert component._filter_rows([row], "E11.9") == [row]
    assert component._filter_rows([row], "диабет") == [row]


def _dashboard(*visits: VisitSummary) -> DashboardResponse:
    return DashboardResponse(
        generated_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        patient=DashboardPatient(id="patient-1", full_name="Пациент"),
        visits=list(visits),
    )
