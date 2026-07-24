"""History-based follow-up rules."""

from __future__ import annotations

from datetime import date, datetime

from src.contracts.dashboard.v1 import RedFlag
from src.contracts.patient.v1 import PatientRecord

from .common import format_observed_at


def evaluate_follow_up_flags(
    record: PatientRecord,
    *,
    as_of: date,
) -> list[RedFlag]:
    """Evaluate follow-up gaps that can be supported by the available record."""

    if not _has_diabetes(record):
        return []
    ophthalmology_dates = [
        occurred
        for encounter in record.encounters
        if _is_ophthalmology(encounter.practitioner.specialty)
        and (occurred := _as_date(encounter.occurred_at)) is not None
        and occurred <= as_of
    ]
    interval_years = 1 if _has_retinopathy(record) else 2
    if ophthalmology_dates:
        latest = max(ophthalmology_dates)
        if _whole_years(latest, as_of) < interval_years:
            return []
        explanation = (
            f"Последний приём офтальмолога в доступной истории — "
            f"{format_observed_at(latest)}; к {format_observed_at(as_of)} "
            f"прошло не менее {interval_years} "
            f"{'года' if interval_years == 2 else 'года'}."
        )
    else:
        explanation = (
            "В доступной истории пациента с диабетом нет датированного "
            "приёма офтальмолога."
        )
    return [
        RedFlag(
            code="diabetes-ophthalmology-follow-up-gap",
            severity="warning",
            title="Нет актуального офтальмологического наблюдения",
            explanation=(
                f"{explanation} Флаг оценивает только полноту выгрузки и не "
                "доказывает, что осмотр не проводился вне этой МИС."
            ),
        )
    ]


def _has_diabetes(record: PatientRecord) -> bool:
    return any(
        (condition.coding.code or "").upper().startswith(("E10", "E11"))
        or "диабет" in condition.coding.display.casefold()
        for condition in record.conditions
    )


def _has_retinopathy(record: PatientRecord) -> bool:
    return any(
        (condition.coding.code or "").upper().startswith(("H35", "H36"))
        or "ретинопат" in condition.coding.display.casefold()
        for condition in record.conditions
    )


def _is_ophthalmology(specialty: str | None) -> bool:
    return specialty is not None and "офтальм" in specialty.casefold()


def _as_date(value: date | datetime | None) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    return value


def _whole_years(start: date, end: date) -> int:
    return end.year - start.year - (
        (end.month, end.day) < (start.month, start.day)
    )
