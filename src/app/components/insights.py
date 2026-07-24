"""Compact red flags and AI summary sections."""

from __future__ import annotations

from html import escape
import re

import streamlit as st

from src.app.theme import render_section_header
from src.contracts.dashboard.v1 import DashboardResponse, RedFlag


_SEVERITY_META = {
    "critical": ("Критический сигнал", "critical", "Срочно"),
    "warning": ("Требует внимания", "warning", "Внимание"),
    "info": ("Информация", "info", "К сведению"),
}
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[А-ЯA-ZЁ])")


def render_insights(dashboard: DashboardResponse) -> None:
    """Display backend insights without calculating or generating them."""

    render_red_flags(dashboard)
    render_ai_summary(dashboard)


def render_red_flags(dashboard: DashboardResponse) -> None:
    """Display concise signals with their full rationale on demand."""

    render_section_header(
        "Требует внимания",
        eyebrow="КЛИНИЧЕСКИЕ СИГНАЛЫ",
        description=(
            "Детерминированные правила выделяют факты для проверки, "
            "но не заменяют решение врача."
        ),
    )
    if not dashboard.red_flags:
        st.markdown(
            """
            <div class="mis-no-signals mis-enter">
              <span>✓</span>
              <div>
                <strong>Активных сигналов нет</strong>
                <p>По доступным данным правила красных флагов не сработали.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    columns = st.columns(min(2, len(dashboard.red_flags)), gap="medium")
    for index, flag in enumerate(dashboard.red_flags):
        card = columns[index % len(columns)].container(border=True)
        _render_flag_card(card, flag)


def _render_flag_card(card: object, flag: RedFlag) -> None:
    label, css_class, badge = _SEVERITY_META[flag.severity]
    summary, details = _split_explanation(flag.explanation)
    card.markdown(
        (
            f'<span class="mis-flag-marker mis-flag-{css_class}"></span>'
            f'<article class="mis-flag-card mis-flag-{css_class} mis-enter">'
            '<div class="mis-flag-topline">'
            f"<span>{escape(label)}</span>"
            f"<b>{escape(badge)}</b>"
            "</div>"
            f"<h3>{escape(flag.title)}</h3>"
            f"<p>{escape(summary)}</p>"
            "</article>"
        ),
        unsafe_allow_html=True,
    )
    if details:
        with card.expander("Почему сработало правило"):
            st.write(details)
            st.caption(f"Код правила: {flag.code}")


def _split_explanation(explanation: str) -> tuple[str, str]:
    """Keep the first sentence visible and move supporting caveats on demand."""

    parts = _SENTENCE_BOUNDARY.split(explanation.strip(), maxsplit=1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def render_ai_summary(dashboard: DashboardResponse) -> None:
    """Display a previously generated summary from DashboardResponse v1."""

    render_section_header(
        "ИИ-сводка",
        eyebrow="СВОБОДНЫЙ ТЕКСТ",
        description=(
            "Gemini анализирует жалобы, анамнез и заключения исследований; "
            "числовые тренды остаются на графиках."
        ),
    )
    if dashboard.ai_summary:
        with st.container(border=True):
            st.markdown(
                '<span class="mis-summary-marker"></span>',
                unsafe_allow_html=True,
            )
            st.write(dashboard.ai_summary)
    else:
        st.markdown(
            """
            <div class="mis-summary-empty mis-enter">
              Сводка ещё не сформирована. Запрос запускается только по кнопке.
            </div>
            """,
            unsafe_allow_html=True,
        )
