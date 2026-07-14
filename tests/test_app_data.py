"""Tests for the Streamlit upload data boundary."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.app import data
from src.contracts.dashboard.v1 import DashboardResponse


@pytest.fixture(autouse=True)
def clear_dashboard_cache() -> None:
    data._build_dashboard_payload.clear()


def test_build_dashboard_parses_raw_mis_export() -> None:
    dashboard = data.build_dashboard(
        b'{"PATIENT_INFO":{"pat_id":"patient-1","FIO":"Ivanov Ivan"}}'
    )

    assert isinstance(dashboard, DashboardResponse)
    assert dashboard.schema_version == "1.0"
    assert dashboard.patient.id == "patient-1"
    assert dashboard.patient.full_name == "Ivanov Ivan"


def test_build_dashboard_reports_invalid_json() -> None:
    with pytest.raises(ValueError, match="Invalid JSON"):
        data.build_dashboard(b"{broken")


def test_build_dashboard_accepts_empty_export() -> None:
    dashboard = data.build_dashboard(b"{}")

    assert dashboard.patient.id == "patient"
    assert dashboard.patient.full_name == ""
    assert dashboard.metrics == []
    assert dashboard.visits == []


def test_build_dashboard_removes_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    named_temporary_file = tempfile.NamedTemporaryFile

    def temporary_file_in_test_directory(**kwargs: object):
        return named_temporary_file(dir=tmp_path, **kwargs)

    monkeypatch.setattr(data.tempfile, "NamedTemporaryFile", temporary_file_in_test_directory)

    data.build_dashboard(
        b'{"PATIENT_INFO":{"pat_id":"cleanup-test","FIO":"Cleanup"}}'
    )

    assert list(tmp_path.iterdir()) == []
