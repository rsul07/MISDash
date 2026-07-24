"""Tests for the Streamlit upload data boundary."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.app import data
from src.contracts.dashboard.v1 import DashboardResponse
from src.contracts.patient.v1 import PatientRecord
from src.generator import GenerationConfig, generate_json_bytes


@pytest.fixture(autouse=True)
def clear_dashboard_cache() -> None:
    data._build_pipeline_payload.clear()


def test_build_pipeline_returns_both_typed_results() -> None:
    record, dashboard = data.build_pipeline(
        b'{"PATIENT_INFO":{"pat_id":"patient-1","FIO":"Ivanov Ivan"}}'
    )

    assert isinstance(record, PatientRecord)
    assert isinstance(dashboard, DashboardResponse)
    assert record.patient.id == dashboard.patient.id == "patient-1"
    assert record.patient.full_name == dashboard.patient.full_name == "Ivanov Ivan"


def test_generated_export_traverses_real_pipeline() -> None:
    file_bytes = generate_json_bytes(
        GenerationConfig(seed=7, years=1, light=True)
    )

    record, dashboard = data.build_pipeline(file_bytes)

    assert record.patient.id == dashboard.patient.id == "0004512-К"
    assert record.encounters
    assert record.observations
    assert dashboard.metrics


def test_build_dashboard_parses_raw_mis_export() -> None:
    dashboard = data.build_dashboard(
        b'{"PATIENT_INFO":{"pat_id":"patient-1","FIO":"Ivanov Ivan"}}'
    )

    assert isinstance(dashboard, DashboardResponse)
    assert dashboard.schema_version == "1.1"
    assert dashboard.patient.id == "patient-1"
    assert dashboard.patient.full_name == "Ivanov Ivan"


def test_build_patient_record_reuses_canonical_upload_boundary() -> None:
    record = data.build_patient_record(
        b'{"PATIENT_INFO":{"pat_id":"patient-1","FIO":"Ivanov Ivan"}}'
    )

    assert isinstance(record, PatientRecord)
    assert record.patient.id == "patient-1"


def test_build_pipeline_parses_same_bytes_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    parse_record = data.MISParser.parse_record

    def counted_parse_record(parser: data.MISParser) -> PatientRecord:
        nonlocal calls
        calls += 1
        return parse_record(parser)

    monkeypatch.setattr(data.MISParser, "parse_record", counted_parse_record)
    file_bytes = (
        b'{"PATIENT_INFO":{"pat_id":"cache-test","FIO":"Cache Test"}}'
    )

    first = data.build_pipeline(file_bytes)
    second = data.build_pipeline(file_bytes)

    assert calls == 1
    assert second == first


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

    data.build_pipeline(
        b'{"PATIENT_INFO":{"pat_id":"cleanup-test","FIO":"Cleanup"}}'
    )

    assert list(tmp_path.iterdir()) == []
