"""Rules for the latest clinically relevant laboratory values."""

from __future__ import annotations

from collections.abc import Iterable

from src.contracts.dashboard.v1 import MetricSeries, RedFlag
from src.contracts.patient.v1 import Condition

from .common import format_observed_at, format_value, latest_point


_ASCVD_PREFIXES = (
    "I20",
    "I21",
    "I22",
    "I23",
    "I24",
    "I25",
    "I63",
    "I69",
    "I70",
)


def evaluate_laboratory_flags(
    metrics: list[MetricSeries],
    conditions: Iterable[Condition],
) -> list[RedFlag]:
    """Evaluate conservative rules based on the latest available values."""

    flags: list[RedFlag] = []
    flags.extend(_potassium_flag(metrics))
    flags.extend(_hba1c_flag(metrics))
    flags.extend(_egfr_flag(metrics))
    flags.extend(_ldl_flag(metrics, conditions))
    return flags


def _potassium_flag(metrics: list[MetricSeries]) -> list[RedFlag]:
    point = latest_point(metrics, "potassium")
    if point is None or point.value <= 5.5:
        return []
    severity = "critical" if point.value >= 6.5 else "warning"
    return [
        RedFlag(
            code="latest-potassium-above-5-5",
            severity=severity,
            title="Повышенный калий",
            explanation=(
                f"Последнее значение {format_value(point.value)} mmol/L "
                f"от {format_observed_at(point.observed_at)} превышает "
                "порог 5,5 mmol/L. Нужны клиническая оценка и проверка "
                "достоверности результата."
            ),
        )
    ]


def _hba1c_flag(metrics: list[MetricSeries]) -> list[RedFlag]:
    point = latest_point(metrics, "hba1c")
    if point is None or point.value <= 8.0:
        return []
    return [
        RedFlag(
            code="latest-hba1c-above-8",
            severity="warning",
            title="HbA1c выше 8%",
            explanation=(
                f"Последнее значение {format_value(point.value)}% "
                f"от {format_observed_at(point.observed_at)}. Цель HbA1c "
                "индивидуальна; флаг отмечает значение выше 8%, а не "
                "заменяет оценку врача."
            ),
        )
    ]


def _egfr_flag(metrics: list[MetricSeries]) -> list[RedFlag]:
    point = latest_point(metrics, "egfr-ckd-epi-2021")
    if point is None or point.value >= 45.0:
        return []
    severity = "critical" if point.value < 30.0 else "warning"
    return [
        RedFlag(
            code="latest-egfr-below-45",
            severity=severity,
            title="Сниженная расчётная СКФ",
            explanation=(
                f"Последняя eGFR CKD-EPI 2021 — "
                f"{format_value(point.value)} mL/min/1.73m² "
                f"от {format_observed_at(point.observed_at)}, ниже "
                "45 mL/min/1.73m². Одно расчётное значение не подтверждает "
                "хроническое заболевание."
            ),
        )
    ]


def _ldl_flag(
    metrics: list[MetricSeries],
    conditions: Iterable[Condition],
) -> list[RedFlag]:
    if not _has_documented_ascvd(conditions):
        return []
    point = latest_point(metrics, "ldl-cholesterol")
    if point is None or point.value <= 1.4:
        return []
    return [
        RedFlag(
            code="latest-ldl-above-ascvd-target",
            severity="warning",
            title="ЛПНП выше цели при документированном ССЗ",
            explanation=(
                f"Последний ЛПНП {format_value(point.value)} mmol/L "
                f"от {format_observed_at(point.observed_at)} выше цели "
                "<1,4 mmol/L для очень высокого сердечно-сосудистого риска. "
                "Категория применена только из-за диагноза ССЗ в карте."
            ),
        )
    ]


def _has_documented_ascvd(conditions: Iterable[Condition]) -> bool:
    for condition in conditions:
        code = (condition.coding.code or "").upper().replace(".", "")
        if code.startswith(_ASCVD_PREFIXES):
            return True
    return False
