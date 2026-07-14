"""Tests for clinical metric chart rendering."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from src.app.components import metrics as component
from src.contracts.dashboard.v1 import (
    DashboardPatient,
    DashboardResponse,
    MetricPoint,
    MetricSeries,
)


def test_metrics_use_stable_codes_and_separate_incompatible_units(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)
    dashboard = _dashboard(
        _series("diastolic", "Диастолическое АД", "mmHg", 80),
        _series("systolic", "Систолическое АД", "mmHg", 120),
        _series("glucose", "Глюкоза крови", "mmol/L", 6.5),
        _series("hba1c", "Гликированный гемоглобин", "%", 7.1),
        _series("oxygen-saturation", "Сатурация", "%", 98),
    )

    component.render_metrics(dashboard)

    assert [call.args[0] for call in streamlit.subheader.call_args_list] == [
        "АД и пульс",
        "Диабет",
        "Почки",
        "Липиды",
        "Вес и BMI",
    ]
    figures = [call.args[0] for call in streamlit.plotly_chart.call_args_list]
    assert len(figures) == 3
    assert [trace.name for trace in figures[0].data] == [
        "Систолическое АД",
        "Диастолическое АД",
    ]
    assert figures[0].data[0].type == "scattergl"
    assert list(figures[0].data[0].y) == [120]
    assert figures[1].layout.yaxis.title.text == "mmol/L"
    assert figures[2].layout.yaxis.title.text == "%"
    assert all(
        call.kwargs["use_container_width"] is True
        for call in streamlit.plotly_chart.call_args_list
    )


def test_metrics_handle_missing_series_and_empty_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(component, "st", streamlit)
    dashboard = _dashboard(
        MetricSeries(
            code="glucose",
            display="Глюкоза крови",
            unit="mmol/L",
        )
    )

    component.render_metrics(dashboard)

    streamlit.plotly_chart.assert_not_called()
    assert streamlit.info.call_count == len(component.METRIC_GROUPS)


def _dashboard(*metrics: MetricSeries) -> DashboardResponse:
    return DashboardResponse(
        generated_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        patient=DashboardPatient(id="patient-1", full_name="Пациент"),
        metrics=list(metrics),
    )


def _series(
    code: str,
    display: str,
    unit: str,
    value: float,
) -> MetricSeries:
    return MetricSeries(
        code=code,
        display=display,
        unit=unit,
        points=[
            MetricPoint(
                observed_at=date(2026, 7, 1),
                value=value,
                source_category="laboratory",
            )
        ],
    )
