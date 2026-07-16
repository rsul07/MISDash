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


@st.cache_data(show_spinner=False)
def _build_patient_payload(file_bytes: bytes) -> dict[str, Any]:
    """Parse uploaded bytes once and return a cache-friendly canonical payload."""

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temporary:
            temporary.write(file_bytes)
            temporary_path = Path(temporary.name)

        record = MISParser(temporary_path).parse_record()
        return record.model_dump(mode="json")
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def build_patient_record(file_bytes: bytes) -> PatientRecord:
    """Build a typed canonical record from an uploaded raw MIS export."""

    return PatientRecord.model_validate(_build_patient_payload(file_bytes))


@st.cache_data(show_spinner=False)
def _build_dashboard_payload(file_bytes: bytes) -> dict[str, Any]:
    record = build_patient_record(file_bytes)
    return DashboardService().build(record).model_dump(mode="json")


def build_dashboard(file_bytes: bytes) -> DashboardResponse:
    """Build a typed dashboard response from an uploaded raw MIS export."""

    payload = _build_dashboard_payload(file_bytes)
    return DashboardResponse.model_validate(payload)
