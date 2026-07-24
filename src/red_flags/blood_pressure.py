"""Rule for markedly elevated paired blood-pressure measurements."""

from __future__ import annotations

from src.contracts.dashboard.v1 import MetricPoint, MetricSeries, RedFlag

from .common import date_key, format_observed_at, format_value


def evaluate_blood_pressure_flags(
    metrics: list[MetricSeries],
) -> list[RedFlag]:
    """Flag the latest paired measurement at or above the severe threshold."""

    pair = _latest_pair(metrics)
    if pair is None:
        return []
    systolic, diastolic = pair
    if systolic.value < 180.0 and diastolic.value < 120.0:
        return []
    return [
        RedFlag(
            code="latest-blood-pressure-markedly-high",
            severity="critical",
            title="Очень высокое артериальное давление",
            explanation=(
                f"Последнее парное измерение "
                f"{format_value(systolic.value)}/"
                f"{format_value(diastolic.value)} mmHg "
                f"от {format_observed_at(systolic.observed_at)} достигает "
                "порога 180 САД или 120 ДАД. Само число не устанавливает "
                "гипертонический криз: требуются оценка симптомов и повторное "
                "корректное измерение."
            ),
        )
    ]


def _latest_pair(
    metrics: list[MetricSeries],
) -> tuple[MetricPoint, MetricPoint] | None:
    systolic = _points_by_source(metrics, "systolic")
    diastolic = _points_by_source(metrics, "diastolic")
    pairs: list[tuple[MetricPoint, MetricPoint]] = []
    for source_id, systolic_point in systolic.items():
        diastolic_point = diastolic.get(source_id)
        if (
            diastolic_point is not None
            and diastolic_point.observed_at == systolic_point.observed_at
        ):
            pairs.append((systolic_point, diastolic_point))
    if not pairs:
        return None
    return max(pairs, key=lambda pair: date_key(pair[0].observed_at))


def _points_by_source(
    metrics: list[MetricSeries],
    code: str,
) -> dict[str, MetricPoint]:
    series = next((item for item in metrics if item.code == code), None)
    if series is None:
        return {}
    result: dict[str, MetricPoint] = {}
    for point in series.points:
        for source_id in point.source_ids:
            result[source_id] = point
    return result
