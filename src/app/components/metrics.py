"""Clinical metric charts rendered from DashboardResponse v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from html import escape

import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    AMBER,
    BLUE,
    BORDER,
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
RANGE_SELECTOR_BUTTONS = (
    {"count": 3, "label": "3 мес", "step": "month", "stepmode": "backward"},
    {"count": 1, "label": "1 год", "step": "year", "stepmode": "backward"},
    {"count": 3, "label": "3 года", "step": "year", "stepmode": "backward"},
    {"label": "Всё", "step": "all"},
)
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
    render_section_header(
        "Динамика показателей",
        eyebrow="ВРЕМЕННЫЕ РЯДЫ",
        description=(
            "Выберите клиническую область. Для плотных дневников "
            "по умолчанию показаны последние 90 дней."
        ),
    )

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
            for figure_index, figure in enumerate(_build_figures(series)):
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
    return [
        metrics_by_code[code]
        for code in group.codes
        if code in metrics_by_code
    ]


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
        color = METRIC_COLORS.get(item.code, BLUE)
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
                        if item.calculation is not None
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
                line={"color": color, "width": 2.35},
                marker={
                    "size": 5.5,
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

    xaxis: dict[str, object] = {
        "title": "Дата",
        "rangeselector": {"buttons": RANGE_SELECTOR_BUTTONS},
    }
    default_range = _default_date_range(series)
    if default_range is not None:
        xaxis["range"] = default_range

    figure.update_layout(
        height=390,
        hovermode="closest",
        title={
            "text": f"Динамика · {unit_label or 'без единицы'}",
            "x": 0.025,
            "xanchor": "left",
            "font": {"size": 16, "color": INK},
        },
        legend={
            "title": {"text": ""},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"color": MUTED, "size": 11},
        },
        margin={"l": 54, "r": 24, "t": 78, "b": 48},
        xaxis=xaxis,
        yaxis={
            "title": {"text": unit or "Значение", "font": {"color": MUTED}},
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
        title_font={"color": MUTED},
        rangeselector={
            "buttons": RANGE_SELECTOR_BUTTONS,
            "bgcolor": "#F0F6F8",
            "activecolor": "#DDECF0",
            "bordercolor": BORDER,
            "borderwidth": 1,
            "font": {"color": INK, "size": 10},
        },
    )
    return figure


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
            column.markdown(
                (
                    '<div class="mis-latest-value mis-enter">'
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
    observed_at = [
        _as_utc_naive(point.observed_at)
        for item in series
        for point in item.points
    ]
    if not observed_at:
        return None

    latest = max(observed_at)
    earliest = min(observed_at)
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


def _as_utc_naive(value: date | datetime) -> datetime:
    if not isinstance(value, datetime):
        return datetime.combine(value, time.min)
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
