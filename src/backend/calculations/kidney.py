"""Build eGFR values from dated serum-creatinine observations."""

from __future__ import annotations

from datetime import date, datetime

from src.calculators import (
    CalculatedValue,
    EGFR_CKD_EPI_2021,
    calculate_egfr_ckd_epi_2021,
    classify_egfr_category,
)
from src.contracts.patient.v1 import PatientRecord

from ..measurements import metric_code


def calculate_egfr_metrics(record: PatientRecord) -> list[CalculatedValue]:
    """Calculate adult eGFR for safe serum-creatinine observations."""

    birth_date = record.patient.birth_date
    sex = record.patient.gender
    if birth_date is None or sex not in {"female", "male"}:
        return []

    urine_reports = {
        report.id
        for report in record.diagnostic_reports
        if report.specimen and "моч" in report.specimen.casefold()
    }
    values: list[CalculatedValue] = []
    for observation in record.observations:
        if (
            observation.category != "laboratory"
            or observation.observed_at is None
            or observation.value is None
            or observation.report_id in urine_reports
            or metric_code(observation.coding) != "creatinine"
        ):
            continue
        quantity = observation.value
        if not isinstance(quantity.value, (int, float)) or quantity.unit is None:
            continue
        age = _age_on(birth_date, observation.observed_at)
        if age is None:
            continue
        try:
            value = calculate_egfr_ckd_epi_2021(
                creatinine=float(quantity.value),
                creatinine_unit=quantity.unit,
                age=age,
                sex=sex,
            )
        except ValueError:
            continue
        values.append(
            CalculatedValue(
                definition=EGFR_CKD_EPI_2021,
                observed_at=observation.observed_at,
                value=round(value, 2),
                source_ids=(observation.id,),
                interpretation=classify_egfr_category(value),
            )
        )
    return values


def _age_on(birth_date: date, observed_at: date | datetime) -> int | None:
    observed_date = (
        observed_at.date() if isinstance(observed_at, datetime) else observed_at
    )
    if observed_date < birth_date:
        return None
    return observed_date.year - birth_date.year - (
        (observed_date.month, observed_date.day)
        < (birth_date.month, birth_date.day)
    )
