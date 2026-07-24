"""Synthetic self-monitoring diaries."""

from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

from .distortions import messy_date, messy_num, maybe_missing
from .models import GenerationWindow


def build_diaries(
    rnd: random.Random,
    window: GenerationWindow,
    years: int,
) -> dict[str, list[dict[str, Any]]]:
    blood_pressure: list[dict[str, Any]] = []
    glycemia: list[dict[str, Any]] = []
    diary_years = min(6, years)
    current = window.end - timedelta(days=int(diary_years * 365.25))
    while current < window.end:
        fraction = window.fraction(current)
        for measured_time, period in [
            ((7, 30), "утро"),
            ((14, 0), "день"),
            ((21, 40), "вечер"),
        ]:
            if rnd.random() < 0.18:
                continue
            measured_at = current.replace(
                hour=measured_time[0], minute=measured_time[1]
            ) + timedelta(minutes=rnd.randint(-40, 40))
            blood_pressure.append(
                {
                    "dt": messy_date(
                        measured_at,
                        rnd,
                        styles=["isoT", "unix_str"],
                    ),
                    "sys": messy_num(
                        int(
                            142
                            + 20 * fraction
                            + (6 if period == "утро" else 0)
                            + rnd.gauss(0, 10)
                        ),
                        rnd,
                    ),
                    "dia": messy_num(
                        int(86 + 7 * fraction + rnd.gauss(0, 6)), rnd
                    ),
                    "pulse": rnd.randint(58, 92),
                    "period_dnya": period,
                    "istochnik": rnd.choice(
                        [
                            "app:MedControl",
                            "app:MedControl",
                            "ручной ввод регистратором",
                        ]
                    ),
                    "device_id": maybe_missing(
                        "OMRON-M3-8842", rnd, 0.3
                    ),
                }
            )
        for measured_time, condition in [
            ((7, 0), "натощак"),
            ((20, 0), "перед сном"),
        ]:
            if rnd.random() < 0.35:
                continue
            measured_at = current.replace(
                hour=measured_time[0], minute=measured_time[1]
            ) + timedelta(minutes=rnd.randint(-30, 30))
            glycemia.append(
                {
                    "izmereno": messy_date(
                        measured_at,
                        rnd,
                        styles=["isoT", "iso"],
                    ),
                    "glukoza_mmol": messy_num(
                        round(
                            (
                                6.3
                                if condition == "натощак"
                                else 7.6
                            )
                            + 1.4 * fraction
                            + rnd.gauss(0, 0.9),
                            1,
                        ),
                        rnd,
                    ),
                    "usloviya": condition,
                    "glukometr": "Contour Plus",
                }
            )
        current += timedelta(days=1)
    return {
        "AD_izmereniya": blood_pressure,
        "glikemiya": glycemia,
    }
