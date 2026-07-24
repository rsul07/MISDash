"""Minimal Streamlit entry point for the patient dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pydantic import ValidationError


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.app.components import (
    render_ai_summary,
    render_metrics,
    render_patient_card,
    render_red_flags,
    render_visits,
)
from src.app.data import build_pipeline
from src.app.source import render_patient_source
from src.app.summary import render_summary_controls


st.set_page_config(page_title="MIS Dash")
st.title("MIS Dash")

patient_input = render_patient_source()

if patient_input is not None:
    file_bytes = patient_input.file_bytes
    try:
        with st.spinner("Обрабатываем данные пациента…"):
            record, dashboard = build_pipeline(file_bytes)
    except (ValueError, ValidationError, OSError) as error:
        st.error(f"Не удалось обработать файл: {error}")
    else:
        st.success("Данные пациента успешно обработаны.")
        render_patient_card(dashboard)
        render_metrics(dashboard)
        render_visits(dashboard)
        render_red_flags(dashboard)
        dashboard = render_summary_controls(file_bytes, record, dashboard)
        render_ai_summary(dashboard)
