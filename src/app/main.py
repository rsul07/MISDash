"""Minimal Streamlit entry point for the patient dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from pydantic import ValidationError


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

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
