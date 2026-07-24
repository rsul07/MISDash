"""On-demand Streamlit orchestration for Gemini summaries."""

from __future__ import annotations

from hashlib import sha256

import streamlit as st

from src.app.theme import render_section_header
from src.contracts.dashboard.v1 import DashboardResponse
from src.contracts.patient.v1 import PatientRecord
from src.summarizer import (
    GeminiSummaryClient,
    SummarizerError,
    SummaryService,
    SummarySettings,
    format_summary,
)
from src.summarizer.prompt import PROMPT_VERSION


_STATE_KEY = "clinical_summary_key"
_STATE_MARKDOWN = "clinical_summary_markdown"
_PRIVACY_NOTE = (
    "Gemini Free Tier используется только с синтетическими данными. "
    "Не загружайте реальные медицинские данные."
)


def render_summary_controls(
    file_bytes: bytes,
    record: PatientRecord,
    dashboard: DashboardResponse,
    *,
    settings: SummarySettings | None = None,
    service: SummaryService | None = None,
) -> DashboardResponse:
    """Render an explicit action and attach a session-cached Markdown summary."""

    settings = settings or SummarySettings.from_env()
    cache_key = _summary_cache_key(file_bytes, settings.model)
    if st.session_state.get(_STATE_KEY) != cache_key:
        st.session_state[_STATE_KEY] = cache_key
        st.session_state.pop(_STATE_MARKDOWN, None)

    render_section_header(
        "ИИ-сводка",
        description=(
            "Gemini анализирует жалобы, анамнез и заключения исследований; "
            "числовые тренды остаются на графиках."
        ),
    )
    st.caption(_PRIVACY_NOTE)
    if settings.api_key is None and service is None:
        st.warning(
            "Для генерации сводки добавьте GEMINI_API_KEY в локальный файл .env."
        )

    button_label = (
        "Сформировать заново"
        if _STATE_MARKDOWN in st.session_state
        else "Сформировать ИИ-сводку"
    )
    should_generate = st.button(
        button_label,
        disabled=settings.api_key is None and service is None,
        type="primary",
        icon=":material/auto_awesome:",
        width="stretch",
    )
    if should_generate:
        try:
            summary_service = service or SummaryService(
                GeminiSummaryClient.from_settings(settings)
            )
            with st.spinner("Gemini формирует краткую сводку…"):
                summary = summary_service.summarize(record, dashboard)
            st.session_state[_STATE_MARKDOWN] = format_summary(summary)
        except SummarizerError as error:
            st.warning(str(error))

    markdown = st.session_state.get(_STATE_MARKDOWN)
    if isinstance(markdown, str) and markdown:
        return dashboard.model_copy(update={"ai_summary": markdown})
    return dashboard.model_copy(update={"ai_summary": None})


def _summary_cache_key(file_bytes: bytes, model: str) -> str:
    file_digest = sha256(file_bytes).hexdigest()
    return f"{file_digest}:{model}:{PROMPT_VERSION}"
