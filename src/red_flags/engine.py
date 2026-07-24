"""Composition root for deterministic clinical red flags."""

from __future__ import annotations

from datetime import date

from src.contracts.dashboard.v1 import MetricSeries, RedFlag
from src.contracts.patient.v1 import PatientRecord

from .blood_pressure import evaluate_blood_pressure_flags
from .follow_up import evaluate_follow_up_flags
from .laboratory import evaluate_laboratory_flags


_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def evaluate_red_flags(
    record: PatientRecord,
    metrics: list[MetricSeries],
    *,
    as_of: date,
) -> list[RedFlag]:
    """Run all rules and return a stable severity-first list."""

    flags = [
        *evaluate_blood_pressure_flags(metrics),
        *evaluate_laboratory_flags(metrics, record.conditions),
        *evaluate_follow_up_flags(record, as_of=as_of),
    ]
    return sorted(flags, key=lambda flag: (_SEVERITY_ORDER[flag.severity], flag.code))
