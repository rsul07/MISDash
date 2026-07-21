"""Backend-provided red flags and AI summary sections."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from src.contracts.dashboard.v1 import DashboardResponse


_EMPTY = "Пока нет данных"


def render_insights(dashboard: DashboardResponse) -> None:
    """Display backend insights without calculating or generating them."""

    render_red_flags(dashboard)
    render_ai_summary(dashboard)


def render_red_flags(dashboard: DashboardResponse) -> None:
    """Display deterministic flags supplied by the backend."""

    st.header("Красные флаги")
    if dashboard.red_flags:
        renderers: dict[str, Callable[[str], object]] = {
            "critical": st.error,
            "warning": st.warning,
            "info": st.info,
        }
        for flag in dashboard.red_flags:
            renderers[flag.severity](f"{flag.title} — {flag.explanation}")
    else:
        st.info(_EMPTY)



def render_ai_summary(dashboard: DashboardResponse) -> None:
    """Display a previously generated summary from DashboardResponse v1."""

    st.header("Резюме от ИИ")
    if dashboard.ai_summary:
        st.write(dashboard.ai_summary)
    else:
        st.info(_EMPTY)
