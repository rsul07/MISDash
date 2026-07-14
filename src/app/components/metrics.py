"""Clinical metric charts rendered from DashboardResponse v1."""

from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go
import streamlit as st

from src.contracts.dashboard.v1 import DashboardResponse, MetricSeries


@dataclass(frozen=True)
class MetricGroup:
    title: str
    codes: tuple[str, ...]


METRIC_GROUPS = (
    MetricGroup("АД и пульс", ("systolic", "diastolic", "heart-rate")),
    MetricGroup("Диабет", ("glucose", "hba1c")),
    MetricGroup("Почки", ("creatinine", "potassium")),
    MetricGroup(
        "Липиды",
        (
            "total-cholesterol",
            "ldl-cholesterol",
            "hdl-cholesterol",
            "triglycerides",
        ),
    ),
    MetricGroup("Вес и BMI", ("body-weight", "bmi")),
)


def render_metrics(dashboard: DashboardResponse) -> None:
    """Render supported backend metric series grouped by stable codes."""

    metrics_by_code = {
        series.code: series for series in dashboard.metrics if series.points
    }
    st.header("Динамика показателей")

    for group in METRIC_GROUPS:
        st.subheader(group.title)
        series = [
            metrics_by_code[code] for code in group.codes if code in metrics_by_code
        ]
        if not series:
            st.info("Нет данных для этой группы показателей.")
            continue

        for figure in _build_figures(series):
            st.plotly_chart(
                figure,
                use_container_width=True,
                config={"displayModeBar": False},
            )


def _build_figures(series: list[MetricSeries]) -> list[go.Figure]:
    """Build separate figures for incompatible measurement units."""

    by_unit: dict[str | None, list[MetricSeries]] = {}
    for item in series:
        by_unit.setdefault(item.unit, []).append(item)

    return [
        _build_figure(unit, unit_series)
        for unit, unit_series in by_unit.items()
    ]


def _build_figure(unit: str | None, series: list[MetricSeries]) -> go.Figure:
    figure = go.Figure()
    unit_label = unit or ""

    for item in series:
        figure.add_trace(
            go.Scattergl(
                x=[point.observed_at for point in item.points],
                y=[point.value for point in item.points],
                customdata=[point.source_category for point in item.points],
                mode="lines+markers",
                name=item.display,
                marker={"size": 5},
                hovertemplate=(
                    "Дата: %{x|%d.%m.%Y %H:%M}<br>"
                    f"Значение: %{{y:.2f}} {unit_label}<br>"
                    "Источник: %{customdata}<extra>%{fullData.name}</extra>"
                ),
            )
        )

    figure.update_layout(
        height=360,
        hovermode="closest",
        legend_title_text="Показатель",
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        xaxis_title="Дата",
        yaxis_title=unit or "Значение",
    )
    return figure
