"""Clinical metric charts rendered from DashboardResponse v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from html import escape
from math import ceil

import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    AMBER,
    BLUE,
    CRITICAL,
    INK,
    MUTED,
    TEAL,
    render_section_header,
)
from src.contracts.dashboard.v1 import CalculationInfo, DashboardResponse, MetricSeries


@dataclass(frozen=True)
class MetricGroup:
    key: str
    title: str
    codes: tuple[str, ...]


METRIC_GROUPS = (
    MetricGroup(
        "blood-pressure",
        "Артериальное давление",
        ("systolic", "diastolic", "pulse-pressure"),
    ),
    MetricGroup(
        "glycemic-control",
        "Гликемический контроль",
        ("glucose", "hba1c"),
    ),
    MetricGroup(
        "kidneys",
        "Почки",
        (
            "creatinine",
            "egfr-ckd-epi-2021",
            "urine-albumin-creatinine-ratio",
            "potassium",
        ),
    ),
    MetricGroup(
        "lipids",
        "Липиды",
        (
            "total-cholesterol",
            "non-hdl-cholesterol",
            "ldl-cholesterol",
            "calculated-ldl-cholesterol",
            "hdl-cholesterol",
            "triglycerides",
        ),
    ),
    MetricGroup("weight", "Вес и BMI", ("body-weight", "bmi")),
)

DENSE_SERIES_POINT_THRESHOLD = 500
DEFAULT_VISIBLE_DAYS = 365
DENSE_VISIBLE_DAYS = 90
METRIC_COLORS = {
    "systolic": BLUE,
    "diastolic": TEAL,
    "pulse-pressure": AMBER,
    "glucose": BLUE,
    "hba1c": TEAL,
    "creatinine": BLUE,
    "egfr-ckd-epi-2021": TEAL,
    "urine-albumin-creatinine-ratio": AMBER,
    "potassium": CRITICAL,
    "total-cholesterol": BLUE,
    "non-hdl-cholesterol": TEAL,
    "ldl-cholesterol": AMBER,
    "calculated-ldl-cholesterol": "#B26D18",
    "hdl-cholesterol": "#6677C8",
    "triglycerides": "#3A9CB8",
    "body-weight": BLUE,
    "bmi": TEAL,
}


def render_metrics(dashboard: DashboardResponse) -> None:
    """Render only the selected non-empty clinical metric group."""

    metrics_by_code = {
        series.code: series for series in dashboard.metrics if series.points
    }
    render_section_header("Динамика показателей")

    available_groups = [
        (group, group_series)
        for group in METRIC_GROUPS
        if (group_series := _series_for_group(group, metrics_by_code))
    ]
    if not available_groups:
        st.info("Нет данных для отображения динамики показателей.")
        return

    tabs = st.tabs(
        [group.title for group, _ in available_groups],
        key="metric-group-tabs",
        on_change="rerun",
    )
    for (group, series), tab in zip(available_groups, tabs, strict=True):
        if not tab.open:
            continue

        with tab:
            _render_latest_values(series)
            visible_range = _render_date_range(group, series)
            for figure_index, figure in enumerate(
                _build_figures(series, visible_range)
            ):
                st.plotly_chart(
                    figure,
                    key=f"metric-chart-{group.key}-{figure_index}",
                    width="stretch",
                    config={"displayModeBar": False},
                    theme=None,
                )
            _render_calculation_explanations(series)


def _series_for_group(
    group: MetricGroup,
    metrics_by_code: dict[str, MetricSeries],
) -> list[MetricSeries]:
    series = [
        metrics_by_code[code]
        for code in group.codes
        if code in metrics_by_code
    ]
    return sorted(series, key=lambda item: item.calculation is None)


def _build_figures(
    series: list[MetricSeries],
    visible_range: tuple[datetime, datetime] | None = None,
) -> list[go.Figure]:
    """Build separate figures for incompatible measurement units."""

    by_unit: dict[str | None, list[MetricSeries]] = {}
    for item in series:
        by_unit.setdefault(item.unit, []).append(item)

    return [
        _build_figure(unit, unit_series, visible_range)
        for unit, unit_series in by_unit.items()
    ]


def _build_figure(
    unit: str | None,
    series: list[MetricSeries],
    visible_range: tuple[datetime, datetime] | None = None,
) -> go.Figure:
    figure = go.Figure()
    unit_label = unit or ""

    for item in series:
        color = METRIC_COLORS.get(item.code, BLUE)
        is_calculated = item.calculation is not None
        has_interpretation = any(point.interpretation for point in item.points)
        interpretation_line = (
            "Категория: %{customdata[1]}<br>" if has_interpretation else ""
        )
        figure.add_trace(
            go.Scattergl(
                x=[point.observed_at for point in item.points],
                y=[point.value for point in item.points],
                customdata=[
                    [
                        "Расчётный показатель"
                        if is_calculated
                        else point.source_category,
                        point.interpretation or "",
                    ]
                    for point in item.points
                ],
                mode=(
                    "lines"
                    if len(item.points) > DENSE_SERIES_POINT_THRESHOLD
                    else "lines+markers"
                ),
                name=item.display,
                line={"color": color, "width": 3.6 if is_calculated else 2.35},
                marker={
                    "size": 7 if is_calculated else 5.5,
                    "symbol": "diamond" if is_calculated else "circle",
                    "color": color,
                    "line": {"color": "#FFFFFF", "width": 0.8},
                },
                connectgaps=False,
                hovertemplate=(
                    "Дата: %{x|%d.%m.%Y %H:%M}<br>"
                    f"Значение: %{{y:.2f}} {unit_label}<br>"
                    f"{interpretation_line}"
                    "Источник: %{customdata[0]}<extra>%{fullData.name}</extra>"
                ),
            )
        )

    xaxis: dict[str, object] = {}
    if visible_range is not None:
        xaxis["range"] = visible_range

    legend_rows = max(1, ceil(len(series) / 2))

    figure.update_layout(
        height=390,
        hovermode="closest",
        legend={
            "title": {"text": ""},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "entrywidth": 220,
            "entrywidthmode": "pixels",
            "font": {"color": MUTED, "size": 11},
        },
        margin={
            "l": 48,
            "r": 24,
            "t": 28 + legend_rows * 24,
            "b": 30,
        },
        xaxis=xaxis,
        yaxis={
            "gridcolor": "#E4EDF2",
            "zeroline": False,
            "tickfont": {"color": MUTED},
            "fixedrange": False,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font={"family": "Inter, Segoe UI, sans-serif", "color": INK},
        hoverlabel={
            "bgcolor": INK,
            "bordercolor": INK,
            "font": {"color": "#FFFFFF", "size": 12},
        },
        transition={"duration": 250, "easing": "cubic-in-out"},
    )
    figure.update_xaxes(
        gridcolor="#EEF3F6",
        zeroline=False,
        tickfont={"color": MUTED},
    )
    return figure


def _render_date_range(
    group: MetricGroup,
    series: list[MetricSeries],
) -> tuple[datetime, datetime] | None:
    """Render one shared date range control for every chart in a group."""

    bounds = _date_bounds(series)
    if bounds is None or bounds[0] == bounds[1]:
        return bounds

    default_range = _default_date_range(series) or bounds
    selected = st.slider(
        "Период отображения",
        min_value=bounds[0],
        max_value=bounds[1],
        value=default_range,
        format="DD.MM.YYYY",
        key=f"metric-range-{group.key}",
    )
    if (
        isinstance(selected, tuple)
        and len(selected) == 2
        and all(isinstance(value, datetime) for value in selected)
    ):
        return selected
    return default_range


def _render_latest_values(series: list[MetricSeries]) -> None:
    for start in range(0, len(series), 4):
        batch = series[start : start + 4]
        columns = st.columns(len(batch), gap="small")
        for column, item in zip(columns, batch, strict=True):
            point = max(
                item.points,
                key=lambda candidate: _as_utc_naive(candidate.observed_at),
            )
            unit = f" {escape(item.unit)}" if item.unit else ""
            calculated = (
                '<span class="mis-latest-badge">расчётный</span>'
                if item.calculation is not None
                else ""
            )
            card_class = (
                "mis-latest-value mis-latest-value--calculated mis-enter"
                if item.calculation is not None
                else "mis-latest-value mis-enter"
            )
            column.markdown(
                (
                    f'<div class="{card_class}">'
                    f"<span>{escape(item.display)}</span>"
                    f"<strong>{point.value:g}{unit}</strong>"
                    '<div class="mis-latest-meta">'
                    f"<small>{point.observed_at.strftime('%d.%m.%Y')}</small>"
                    f"{calculated}"
                    "</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def _render_calculation_explanations(series: list[MetricSeries]) -> None:
    for item in series:
        if item.calculation is None:
            continue
        with st.expander(f"Как рассчитан показатель «{item.display}»"):
            _render_calculation_info(item.calculation)
            _render_calculation_example(item)


def _render_calculation_info(info: CalculationInfo) -> None:
    st.markdown(f"**Что это:** {info.description}")
    st.markdown(f"**Для чего:** {info.purpose}")
    st.markdown(f"**Используемые данные:** {', '.join(info.inputs)}")
    st.markdown(f"**Метод:** {info.method}")
    st.markdown(f"**Основание:** {info.standard}")
    if info.limitations:
        st.markdown("**Ограничения:**")
        for limitation in info.limitations:
            st.markdown(f"- {limitation}")
    if info.references:
        links = " · ".join(
            f"[Источник {index}]({url})"
            for index, url in enumerate(info.references, start=1)
        )
        st.markdown(f"**Ссылки:** {links}")


def _render_calculation_example(series: MetricSeries) -> None:
    points = [point for point in series.points if point.calculation_inputs]
    if not points:
        return
    point = max(points, key=lambda item: _as_utc_naive(item.observed_at))
    observed_at = point.observed_at.strftime("%d.%m.%Y")
    st.markdown(f"**Пример по данным пациента от {observed_at}:**")
    for input_value in point.calculation_inputs:
        unit = f" {input_value.unit}" if input_value.unit else ""
        source = (
            f" · источник `{input_value.source_id}`"
            if input_value.source_id
            else ""
        )
        value = _format_input_value(input_value.value)
        st.markdown(f"- {input_value.display}: {value}{unit}{source}")
    result_unit = f" {series.unit}" if series.unit else ""
    st.markdown(f"**Результат:** {_format_input_value(point.value)}{result_unit}")
    if point.interpretation:
        st.markdown(f"**Категория:** {point.interpretation}")


def _format_input_value(value: float | int | str) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _default_date_range(
    series: list[MetricSeries],
) -> tuple[datetime, datetime] | None:
    bounds = _date_bounds(series)
    if bounds is None:
        return None

    earliest, latest = bounds
    visible_days = (
        DENSE_VISIBLE_DAYS
        if any(
            len(item.points) > DENSE_SERIES_POINT_THRESHOLD
            for item in series
        )
        else DEFAULT_VISIBLE_DAYS
    )
    if latest - earliest <= timedelta(days=visible_days):
        return None
    return latest - timedelta(days=visible_days), latest


def _date_bounds(
    series: list[MetricSeries],
) -> tuple[datetime, datetime] | None:
    observed_at = [
        _as_utc_naive(point.observed_at)
        for item in series
        for point in item.points
    ]
    if not observed_at:
        return None
    return min(observed_at), max(observed_at)


def _as_utc_naive(value: date | datetime) -> datetime:
    if not isinstance(value, datetime):
        return datetime.combine(value, time.min)
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
