"""Minimal Streamlit entry point for the patient dashboard."""

from __future__ import annotations

import streamlit as st
from pydantic import ValidationError

from src.app.data import build_dashboard


st.set_page_config(page_title="Пациент за 30 секунд")
st.title("Пациент за 30 секунд")

uploaded_file = st.file_uploader("Загрузите выгрузку пациента", type=["json"])

if uploaded_file is None:
    st.info("Загрузите JSON-файл пациента, чтобы сформировать дашборд.")
else:
    try:
        with st.spinner("Обрабатываем данные пациента…"):
            dashboard = build_dashboard(uploaded_file.getvalue())
    except (ValueError, ValidationError, OSError) as error:
        st.error(f"Не удалось обработать файл: {error}")
    else:
        st.success("Данные пациента успешно обработаны.")
        st.write(dashboard.patient.full_name or "Имя пациента не указано")
