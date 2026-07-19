"""Tests for clinical metric chart rendering."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from src.app.components import metrics as component
from src.contracts.dashboard.v1 import (
    DashboardPatient,
    DashboardResponse,
    MetricPoint,
    MetricSeries,
)


def test_metrics_render_only_active_available_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = MagicMock()
    streamlit.tabs.return_value = [_Tab(open=True), _Tab(open=False)]
    monkeypatch.setattr(component, "st", streamlit)
    dashboard = _dashboard(
        _series("diastolic", "Диастолическое АД", "mmHg", 80),
        _series("systolic", "Систолическое АД", "mmHg", 120),
        _series("heart-rate", "Частота сердечных сокращений", "beats/min", 70),
        _series("glucose", "Глюкоза крови", "mmol/L", 6.5),
        _series("hba1c", "Гликированный гемоглобин", "%", 7.1),
        _series("oxygen-saturation", "Сатурация", "%", 98),
    )

    component.render_metrics(dashboard)

    streamlit.tabs.assert_called_once_with(
        ["АД и пульс", "Диабет"],
        key="metric-group-tabs",
        on_change="rerun",
    )
    figures = [call.args[0] for call in streamlit.plotly_chart.call_args_list]
    assert len(figures) == 1
    assert [trace.name for trace in figures[0].data] == [
        "Систолическое АД",
        "Диастолическое АД",
    ]
    assert figures[0].data[0].type == "scattergl"
    assert list(figures[0].data[0].y) == [120]
    assert [
        call.kwargs["key"] for call in streamlit.plotly_chart.call_args_list
    ] == [
        "metric-chart-blood-pressure-0",
    ]
    assert all(
        call.kwargs["use_container_width"] is True
        for call in streamlit.plotly_chart.call_args_list
    )
    streamlit.info.assert_not_called()


def test_dense_series_use_lines_and_default_to_latest_year() -> None:
    dense = _series(
        "systolic",
        "Систолическое АД",
        "mmHg",
        120,
        point_count=component.DENSE_SERIES_POINT_THRESHOLD + 1,
    )
    sparse = _series(
        "diastolic",
        "Диастолическое АД",
        "mmHg",
        80,
        point_count=2,
    )

    figure = component._build_figure("mmHg", [dense, sparse])

    assert figure.data[0].mode == "lines"
    assert figure.data[1].mode == "lines+markers"
    assert [
        button.label for button in figure.layout.xaxis.rangeselector.buttons
    ] == ["1 год", "3 года", "Всё"]
    visible_range = figure.layout.xaxis.range
    assert visible_range is not None
    assert visible_range[1] - visible_range[0] == timedelta(days=365)


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
    streamlit.tabs.assert_not_called()
    streamlit.info.assert_called_once_with(
        "Нет данных для отображения динамики показателей."
    )


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
    *,
    point_count: int = 1,
) -> MetricSeries:
    return MetricSeries(
        code=code,
        display=display,
        unit=unit,
        points=[
            MetricPoint(
                observed_at=date(2024, 1, 1) + timedelta(days=index),
                value=value,
                source_category="laboratory",
            )
            for index in range(point_count)
        ],
    )


class _Tab:
    def __init__(self, *, open: bool) -> None:
        self.open = open

    def __enter__(self) -> _Tab:
        return self

    def __exit__(self, *_: object) -> None:
        return None
