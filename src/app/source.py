"""Streamlit controls for selecting an uploaded or generated MIS export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import streamlit as st

from src.generator import GenerationConfig, generate_json_bytes


UPLOAD_SOURCE = "Загрузить JSON"
GENERATED_SOURCE = "Сгенерировать синтетическую выгрузку"

_SOURCE_KEY = "patient-source"
_GENERATED_STATE_KEY = "generated-patient"
_GENERATOR_FORM_KEY = "synthetic-patient-form"
_DOWNLOAD_KEY = "download-generated-patient"


@dataclass(frozen=True, slots=True)
class PatientInput:
    """One raw JSON payload selected for the shared parser pipeline."""

    file_bytes: bytes
    filename: str
    origin: Literal["upload", "generated"]


def render_patient_source() -> PatientInput | None:
    """Render source controls and return the currently selected raw export."""

    source = st.radio(
        "Источник данных",
        (UPLOAD_SOURCE, GENERATED_SOURCE),
        horizontal=True,
        key=_SOURCE_KEY,
    )
    if source == UPLOAD_SOURCE:
        return _render_upload()
    return _render_generator()


def _render_upload() -> PatientInput | None:
    uploaded_file = st.file_uploader(
        "Загрузите выгрузку пациента",
        type=["json"],
        key="patient-json-upload",
    )
    if uploaded_file is None:
        st.info("Загрузите JSON-файл пациента, чтобы сформировать дашборд.")
        return None

    raw_name = getattr(uploaded_file, "name", "")
    filename = Path(raw_name).name if isinstance(raw_name, str) else ""
    return PatientInput(
        file_bytes=uploaded_file.getvalue(),
        filename=filename or "patient.json",
        origin="upload",
    )


def _render_generator() -> PatientInput | None:
    with st.form(_GENERATOR_FORM_KEY):
        seed = st.number_input(
            "Seed",
            min_value=0,
            max_value=2_147_483_647,
            value=7,
            step=1,
            help="Одинаковые параметры создают одинаковую синтетическую выгрузку.",
        )
        years = st.slider(
            "Глубина истории, лет",
            min_value=1,
            max_value=9,
            value=3,
        )
        light = st.checkbox(
            "Сокращённые приёмы и исследования",
            value=True,
            help=(
                "Уменьшается число приёмов, лабораторных и инструментальных "
                "исследований."
            ),
        )
        st.caption(
            "Режим light не уменьшает плотность дневников самоконтроля "
            "АД и глюкозы."
        )
        submitted = st.form_submit_button(
            "Сгенерировать и открыть",
            type="primary",
        )

    if submitted:
        config = GenerationConfig(
            seed=int(seed),
            years=int(years),
            light=bool(light),
        )
        with st.spinner("Формируем синтетическую выгрузку…"):
            file_bytes = _generate_json_bytes(config)
        st.session_state[_GENERATED_STATE_KEY] = {
            "file_bytes": file_bytes,
            "filename": _generated_filename(config),
            "seed": config.seed,
            "years": config.years,
            "light": config.light,
        }

    selected = _generated_patient_input()
    if selected is None:
        st.info("Настройте параметры и нажмите «Сгенерировать и открыть».")
        return None

    state = st.session_state[_GENERATED_STATE_KEY]
    mode = "light" if state["light"] else "full"
    st.caption(
        f"Синтетическая выгрузка: seed={state['seed']}, "
        f"{state['years']} лет, {mode}, {_format_size(len(selected.file_bytes))}."
    )
    st.download_button(
        "Скачать исходный JSON",
        data=selected.file_bytes,
        file_name=selected.filename,
        mime="application/json",
        key=_DOWNLOAD_KEY,
    )
    return selected


@st.cache_data(show_spinner=False, max_entries=4)
def _generate_json_bytes(config: GenerationConfig) -> bytes:
    """Cache deterministic generator output independently from UI reruns."""

    return generate_json_bytes(config)


def _generated_patient_input() -> PatientInput | None:
    state = st.session_state.get(_GENERATED_STATE_KEY)
    if not isinstance(state, dict):
        return None
    file_bytes = state.get("file_bytes")
    filename = state.get("filename")
    if (
        not isinstance(file_bytes, bytes)
        or not isinstance(filename, str)
        or type(state.get("seed")) is not int
        or type(state.get("years")) is not int
        or type(state.get("light")) is not bool
    ):
        return None
    return PatientInput(
        file_bytes=file_bytes,
        filename=filename,
        origin="generated",
    )


def _generated_filename(config: GenerationConfig) -> str:
    mode = "light" if config.light else "full"
    return f"patient_seed_{config.seed}_{config.years}y_{mode}.json"


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1_000_000:
        return f"{size_bytes / 1_000:.1f} КБ"
    return f"{size_bytes / 1_000_000:.1f} МБ"
