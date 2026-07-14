"""Visit table rendered from DashboardResponse v1."""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from src.contracts.dashboard.v1 import DashboardResponse, VisitSummary


_MISSING = "Нет данных"


def render_visits(dashboard: DashboardResponse) -> None:
    """Render visits in the recent-first order supplied by the backend."""

    st.header("Врачебные приёмы")
    if not dashboard.visits:
        st.info("Пока нет данных")
        return

    rows = [_visit_row(visit) for visit in dashboard.visits]
    st.dataframe(rows, hide_index=True, use_container_width=True)


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
