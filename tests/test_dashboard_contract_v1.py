"""Executable specification for DashboardResponse v1."""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from src.contracts.dashboard.v1 import (
    CalculationInfo,
    DashboardPatient,
    DashboardResponse,
    MetricPoint,
    MetricSeries,
)


def test_dashboard_response_serializes_generic_backend_projection() -> None:
    response = DashboardResponse(
        generated_at=datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc),
        patient=DashboardPatient(
            id="patient-1",
            full_name="Иванов Иван",
            birth_date=date(1980, 3, 1),
            age=46,
        ),
        metrics=[
            MetricSeries(
                code="glucose",
                display="Глюкоза крови",
                unit="mmol/L",
                points=[
                    MetricPoint(
                        observed_at=date(2026, 7, 1),
                        value=6.5,
                        source_category="laboratory",
                        source_ids=["observation-1"],
                    )
                ],
            )
        ],
    )

    payload = response.model_dump(mode="json")

    assert payload["schema_version"] == "1.0"
    assert payload["generated_at"] == "2026-07-14T10:00:00Z"
    assert payload["patient"]["birth_date"] == "1980-03-01"
    assert payload["metrics"][0]["points"][0]["value"] == 6.5
    assert payload["metrics"][0]["points"][0]["source_ids"] == [
        "observation-1"
    ]
    assert payload["red_flags"] == []
    assert payload["ai_summary"] is None


def test_dashboard_metric_supports_backend_calculation_explanation() -> None:
    series = MetricSeries(
        code="pulse-pressure",
        display="Пульсовое давление",
        unit="mmHg",
        calculation=CalculationInfo(
            code="pulse-pressure",
            description="Разница между САД и ДАД.",
            inputs=["САД", "ДАД"],
            purpose="Показать динамику.",
            method="SBP - DBP",
            standard="ESC 2024",
            limitations=["Не является прямым измерением жёсткости артерий."],
            references=["https://example.test/standard"],
        ),
    )

    assert series.calculation is not None
    assert series.calculation.method == "SBP - DBP"


def test_dashboard_contract_rejects_raw_mis_fields() -> None:
    with pytest.raises(ValidationError):
        DashboardPatient(
            id="patient-1",
            full_name="Иванов Иван",
            JALOBY_TXT="raw MIS field must not leak",
        )


def test_dashboard_contract_rejects_unknown_version() -> None:
    with pytest.raises(ValidationError):
        DashboardResponse(
            schema_version="2.0",
            generated_at=datetime.now(timezone.utc),
            patient=DashboardPatient(id="patient-1", full_name="Иванов Иван"),
        )
