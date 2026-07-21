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
from src.app.data import build_dashboard, build_patient_record
from src.app.summary import render_summary_controls


st.set_page_config(page_title="Пациент за 30 секунд")
st.title("Пациент за 30 секунд")

uploaded_file = st.file_uploader("Загрузите выгрузку пациента", type=["json"])

if uploaded_file is None:
    st.info("Загрузите JSON-файл пациента, чтобы сформировать дашборд.")
else:
    file_bytes = uploaded_file.getvalue()
    try:
        with st.spinner("Обрабатываем данные пациента…"):
            record = build_patient_record(file_bytes)
            dashboard = build_dashboard(file_bytes)
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
