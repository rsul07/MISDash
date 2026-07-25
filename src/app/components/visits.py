"""Searchable visit table rendered from DashboardResponse v1."""

from __future__ import annotations

from datetime import date, datetime
from html import escape

import streamlit as st

from src.app.theme import render_section_header
from src.contracts.dashboard.v1 import CodeLabel, DashboardResponse, VisitSummary


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
    visible_ids = {row["ID"] for row in filtered}
    visible_visits = [
        visit for visit in dashboard.visits if visit.id in visible_ids
    ]
    st.markdown(
        _visit_table_html(visible_visits),
        unsafe_allow_html=True,
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
        "ID": visit.id,
        "Дата": _format_date(visit.occurred_at),
        "Врач": visit.practitioner or _MISSING,
        "Специальность": visit.specialty or _MISSING,
        "Диагнозы": " ".join(
            _diagnosis_text(diagnosis) for diagnosis in visit.diagnoses
        )
        or _MISSING,
        "Жалобы": visit.complaints or _MISSING,
    }


def _format_date(value: date | datetime | None) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return _MISSING


def _diagnosis_text(diagnosis: CodeLabel) -> str:
    if diagnosis.code:
        return f"{diagnosis.code} — {diagnosis.display}"
    return diagnosis.display


def _visit_table_html(visits: list[VisitSummary]) -> str:
    rows = "".join(_visit_table_row(visit) for visit in visits)
    if not rows:
        rows = (
            '<tr><td class="mis-visit-table-empty" colspan="4">'
            "По вашему запросу приёмы не найдены"
            "</td></tr>"
        )
    return (
        '<div class="mis-visit-table-shell mis-enter">'
        '<table class="mis-visit-table" aria-label="Врачебные приёмы">'
        "<thead><tr>"
        "<th>Дата</th><th>Врач</th><th>Диагнозы</th><th>Жалобы</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )


def _visit_table_row(visit: VisitSummary) -> str:
    practitioner = escape(visit.practitioner or _MISSING)
    specialty = escape(visit.specialty or _MISSING)
    complaints = escape(visit.complaints or _MISSING)
    return (
        "<tr>"
        f'<td data-label="Дата">{_visit_date_html(visit.occurred_at)}</td>'
        '<td data-label="Врач"><div class="mis-visit-practitioner">'
        f"<strong>{practitioner}</strong><span>{specialty}</span>"
        "</div></td>"
        f'<td data-label="Диагнозы">{_diagnoses_html(visit.diagnoses)}</td>'
        '<td data-label="Жалобы"><p class="mis-visit-complaints" title="'
        f'{complaints}">{complaints}</p></td>'
        "</tr>"
    )


def _visit_date_html(value: date | datetime | None) -> str:
    if value is None:
        return f'<span class="mis-visit-missing">{_MISSING}</span>'
    day = value.strftime("%d.%m.%Y")
    time_html = (
        f"<small>{value.strftime('%H:%M')}</small>"
        if isinstance(value, datetime)
        else ""
    )
    return f'<div class="mis-visit-date"><strong>{day}</strong>{time_html}</div>'


def _diagnoses_html(diagnoses: list[CodeLabel]) -> str:
    if not diagnoses:
        return f'<span class="mis-visit-missing">{_MISSING}</span>'

    primary, *secondary = diagnoses
    primary_text = escape(_diagnosis_text(primary))
    secondary_html = "".join(
        (
            '<span class="mis-visit-diagnosis-chip" '
            f'title="{escape(_diagnosis_text(diagnosis))}">'
            f"{escape(diagnosis.code or diagnosis.display)}</span>"
        )
        for diagnosis in secondary[:4]
    )
    if len(secondary) > 4:
        hidden = "; ".join(_diagnosis_text(item) for item in secondary[4:])
        secondary_html += (
            '<span class="mis-visit-diagnosis-chip mis-visit-diagnosis-more" '
            f'title="{escape(hidden)}">+{len(secondary) - 4}</span>'
        )
    chips = (
        f'<div class="mis-visit-diagnosis-list">{secondary_html}</div>'
        if secondary_html
        else ""
    )
    return (
        '<div class="mis-visit-diagnoses">'
        '<span class="mis-visit-primary-label">основной</span>'
        f'<strong title="{primary_text}">{primary_text}</strong>'
        f"{chips}</div>"
    )
