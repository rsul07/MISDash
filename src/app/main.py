"""Streamlit entry point for the MIS Dash presentation layer."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pydantic import ValidationError


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.app.dashboard import render_dashboard
from src.app.data import build_pipeline
from src.app.source import render_patient_source
from src.app.theme import (
    apply_app_theme,
    render_app_header,
    render_empty_state,
    render_sidebar_header,
    render_source_status,
)


def run_app() -> None:
    """Configure and render the complete Streamlit application."""

    st.set_page_config(
        page_title="MIS Dash",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={"About": "MIS Dash · синтетический учебный прототип"},
    )
    apply_app_theme()
    render_app_header()

    with st.sidebar:
        render_sidebar_header()
        patient_input = render_patient_source()

    if patient_input is None:
        render_empty_state()
        return

    file_bytes = patient_input.file_bytes
    try:
        with st.spinner("Обрабатываем данные пациента…"):
            record, dashboard = build_pipeline(file_bytes)
    except (ValueError, ValidationError, OSError) as error:
        st.error(f"Не удалось обработать файл: {error}")
    else:
        render_source_status(
            filename=patient_input.filename,
            origin=patient_input.origin,
        )
        render_dashboard(file_bytes, record, dashboard)


if __name__ == "__main__":
    run_app()
