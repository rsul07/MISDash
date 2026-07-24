"""Shared helpers for deterministic red-flag rules."""

from __future__ import annotations

from datetime import date, datetime, time

from src.contracts.dashboard.v1 import MetricPoint, MetricSeries


def latest_point(
    metrics: list[MetricSeries],
    code: str,
) -> MetricPoint | None:
    """Return the chronologically latest point of one metric series."""

    series = next((item for item in metrics if item.code == code), None)
    if series is None or not series.points:
        return None
    return max(series.points, key=lambda item: date_key(item.observed_at))


def format_observed_at(value: date | datetime) -> str:
    """Format a clinical date without leaking an irrelevant midnight time."""

    if isinstance(value, datetime) and value.time() != time.min:
        return value.strftime("%d.%m.%Y %H:%M")
    return value.strftime("%d.%m.%Y")


def format_value(value: float) -> str:
    """Render a compact decimal value for a clinician-facing explanation."""

    return f"{value:.2f}".rstrip("0").rstrip(".")


def date_key(value: date | datetime) -> datetime:
    """Return a timezone-free comparison key for mixed clinical date types."""

    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return datetime.combine(value, datetime.min.time())
