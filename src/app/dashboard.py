"""Dashboard section navigation and presentation composition."""

from __future__ import annotations

import streamlit as st

from src.app.components import (
    render_ai_summary,
    render_metrics,
    render_patient_card,
    render_red_flags,
    render_visits,
)
from src.app.summary import render_summary_controls
from src.contracts.dashboard.v1 import DashboardResponse
from src.contracts.patient.v1 import PatientRecord


OVERVIEW = "Обзор"
METRICS = "Динамика"
VISITS = "Приёмы"
SUMMARY = "ИИ-сводка"
SECTIONS = (OVERVIEW, METRICS, VISITS, SUMMARY)


def render_dashboard(
    file_bytes: bytes,
    record: PatientRecord,
    dashboard: DashboardResponse,
) -> None:
    """Render exactly one top-level section for a clean, stable page."""

    selected = st.segmented_control(
        "Раздел дашборда",
        SECTIONS,
        default=OVERVIEW,
        key="dashboard-section",
        label_visibility="collapsed",
        width="stretch",
    )
    if selected == METRICS:
        render_metrics(dashboard)
    elif selected == VISITS:
        render_visits(dashboard)
    elif selected == SUMMARY:
        dashboard = render_summary_controls(file_bytes, record, dashboard)
        render_ai_summary(dashboard)
    else:
        render_patient_card(dashboard)
        render_red_flags(dashboard)
