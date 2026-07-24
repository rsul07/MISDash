"""Searchable visit table rendered from DashboardResponse v1."""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from src.app.theme import render_section_header
from src.contracts.dashboard.v1 import DashboardResponse, VisitSummary


_MISSING = "Нет данных"


def render_visits(dashboard: DashboardResponse) -> None:
    """Render a compact searchable view of the recent-first visit timeline."""

    render_section_header("Врачебные приёмы")
    if not dashboard.visits:
        st.info("Пока нет данных")
        return

    query = st.text_input(
        "Поиск по приёмам",
        placeholder="Врач, специальность, диагноз или жалоба",
        icon=":material/search:",
    )
    rows = [_visit_row(visit) for visit in dashboard.visits]
    filtered = _filter_rows(rows, query)
    st.caption(f"Показано записей: {len(filtered)} из {len(rows)}")
    st.dataframe(
        filtered,
        hide_index=True,
        width="stretch",
        height=480,
        column_config={
            "Дата": st.column_config.TextColumn("Дата", width="small"),
            "Врач": st.column_config.TextColumn("Врач", width="medium"),
            "Специальность": st.column_config.TextColumn(
                "Специальность",
                width="medium",
            ),
            "Основной диагноз": st.column_config.TextColumn(
                "Основной диагноз",
                width="large",
            ),
            "Жалобы": st.column_config.TextColumn("Жалобы", width="large"),
        },
    )


def _filter_rows(rows: list[dict[str, str]], query: str) -> list[dict[str, str]]:
    normalized = query.casefold().strip()
    if not normalized:
        return rows
    return [
        row
        for row in rows
        if normalized in " ".join(row.values()).casefold()
    ]


def _visit_row(visit: VisitSummary) -> dict[str, str]:
    return {
        "Дата": _format_date(visit.occurred_at),
        "Врач": visit.practitioner or _MISSING,
        "Специальность": visit.specialty or _MISSING,
        "Основной диагноз": _primary_diagnosis(visit),
        "Жалобы": visit.complaints or _MISSING,
    }


def _format_date(value: date | datetime | None) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return _MISSING


def _primary_diagnosis(visit: VisitSummary) -> str:
    if not visit.diagnoses:
        return _MISSING
    diagnosis = visit.diagnoses[0]
    if diagnosis.code:
        return f"{diagnosis.code} — {diagnosis.display}"
    return diagnosis.display
