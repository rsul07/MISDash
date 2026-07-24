"""Data boundary between uploaded MIS exports and the Streamlit UI."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from src.backend import DashboardService
from src.contracts.dashboard.v1 import DashboardResponse
from src.contracts.patient.v1 import PatientRecord
from src.parser import MISParser


PipelinePayload = tuple[dict[str, Any], dict[str, Any]]


@st.cache_data(show_spinner=False, max_entries=4)
def _build_pipeline_payload(file_bytes: bytes) -> PipelinePayload:
    """Run parser and backend once, returning cache-friendly payloads."""

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temporary:
            temporary.write(file_bytes)
            temporary_path = Path(temporary.name)

        record = MISParser(temporary_path).parse_record()
        dashboard = DashboardService().build(record)
        return (
            record.model_dump(mode="json"),
            dashboard.model_dump(mode="json"),
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def build_pipeline(file_bytes: bytes) -> tuple[PatientRecord, DashboardResponse]:
    """Build both typed pipeline results from one dirty MIS export."""

    record_payload, dashboard_payload = _build_pipeline_payload(file_bytes)
    return (
        PatientRecord.model_validate(record_payload),
        DashboardResponse.model_validate(dashboard_payload),
    )


def build_patient_record(file_bytes: bytes) -> PatientRecord:
    """Build a typed canonical record from an uploaded raw MIS export."""

    record_payload, _ = _build_pipeline_payload(file_bytes)
    return PatientRecord.model_validate(record_payload)


def build_dashboard(file_bytes: bytes) -> DashboardResponse:
    """Build a typed dashboard response from an uploaded raw MIS export."""

    _, dashboard_payload = _build_pipeline_payload(file_bytes)
    return DashboardResponse.model_validate(dashboard_payload)
