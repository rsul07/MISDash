"""Synthetic outpatient encounter generation."""

from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

from .catalogs import (
    COMPLAINTS_POOL,
    DOCTORS,
    MEDS_TIMELINE,
    PLAN_POOL,
    STATUS_TEMPLATES,
)
from .distortions import messy_date, messy_num, maybe_missing
from .models import GenerationWindow


def build_encounters(
    rnd: random.Random,
    window: GenerationWindow,
    years: int,
    light: bool,
) -> list[dict[str, Any]]:
    visits: list[dict[str, Any]] = []
    count = years * 9 if not light else years * 4
    visit_dates = sorted(
        window.start
        + timedelta(
            days=rnd.randint(0, int(years * 365.25)),
            hours=rnd.randint(8, 18),
            minutes=rnd.choice([0, 15, 20, 30, 40, 45]),
        )
        for _ in range(count)
    )
    weight0, weight_drift = 89.0, 0.9
    for visit_date in visit_dates:
        fraction = window.fraction(visit_date)
        doctor, specialty = rnd.choice(DOCTORS)
        systolic = int(148 + 18 * fraction + rnd.gauss(0, 9))
        diastolic = int(88 + 6 * fraction + rnd.gauss(0, 6))
        heart_rate = int(72 + rnd.gauss(0, 7))
        weight = round(
            weight0
            + weight_drift * years * fraction
            + rnd.gauss(0, 0.8),
            1,
        )
        bmi = round(weight / (1.76**2), 1)
        complaints = rnd.sample(
            COMPLAINTS_POOL, k=rnd.randint(2, 4)
        )
        complaint_text = "; ".join(
            complaint.format(sys=systolic, dia=diastolic)
            for complaint in complaints
        )
        status = rnd.choice(STATUS_TEMPLATES).format(
            sys=systolic,
            dia=diastolic,
            sys2=systolic - rnd.randint(0, 8),
            dia2=diastolic - rnd.randint(0, 6),
            hr=heart_rate,
            chd=rnd.randint(15, 18),
            bmi=str(bmi).replace(".", ","),
        )
        medications = [
            medicines
            for year, medicines in MEDS_TIMELINE
            if year <= fraction * years
        ][-1]
        therapy_text = "; ".join(
            f"{name} {dose} {frequency}"
            for name, dose, frequency in medications
        )
        anamnesis = (
            "Наблюдается с диагнозами: ГБ II ст., СД 2 типа, ХБП, "
            "дислипидемия. ПИКС (ОИМ 2019 г., стентирование ПКА). "
            "Получает: "
            + therapy_text
            + ". "
            + rnd.choice(
                [
                    "Терапию принимает регулярно.",
                    "Признаётся в пропусках приёма препаратов.",
                    "Самостоятельно отменял статин на 2 мес — «читал про побочки».",
                    "Диету соблюдает частично.",
                    "АД дома не контролирует.",
                ]
            )
        )
        visit = {
            "id_priema": (
                f"VST-{visit_date.strftime('%y%m%d')}-"
                f"{rnd.randint(100, 999)}"
            ),
            "dt_priem": messy_date(visit_date, rnd),
            "VRACH": {
                "fio_doc": doctor,
                "spec_name": specialty,
                "kabinet": str(rnd.randint(101, 428)),
            },
            "vid_priema": rnd.choice(
                [
                    "первичный",
                    "повторный",
                    "повторный",
                    "диспансерный",
                    "проф. осмотр",
                ]
            ),
            "JALOBY_TXT": complaint_text,
            "anamnez_txt": anamnesis,
            "obektivny_status": status,
            "izmereniya": {
                "AD_sist": messy_num(systolic, rnd),
                "AD_diast": messy_num(diastolic, rnd),
                "CHSS": messy_num(heart_rate, rnd),
                "ves": messy_num(weight, rnd),
                "rost": maybe_missing(176, rnd, 0.3),
                "IMT_calc": maybe_missing(
                    messy_num(bmi, rnd), rnd, 0.4
                ),
                "okrujnost_talii_sm": maybe_missing(
                    messy_num(int(102 + 6 * fraction), rnd),
                    rnd,
                    0.55,
                ),
                "SpO2": maybe_missing(rnd.randint(96, 99), rnd, 0.6),
                "temperatura": maybe_missing("36,6", rnd, 0.5),
            },
            "diagnoz_priema": {
                "osnovnoy_MKB": "I11.9",
                "osnovnoy_txt": (
                    "Гипертензивная [гипертоническая] болезнь "
                    "II ст., риск 4"
                ),
                "soputstv": [
                    "E11.9 СД 2 типа",
                    "N18.3 ХБП С3а А2",
                    "E78.2 дислипидемия",
                    "I25.2 ПИКС",
                ],
            },
            "naznacheniya_txt": " ".join(
                rnd.sample(PLAN_POOL, k=rnd.randint(2, 4))
            ),
            "terapiya": [
                {
                    "preparat": name,
                    "doza": dose,
                    "krat": frequency,
                    "forma": "таб.",
                }
                for name, dose, frequency in medications
            ],
            "sled_yavka": messy_date(
                visit_date
                + timedelta(days=rnd.choice([30, 60, 90, 90, 120])),
                rnd,
            ),
            "status_zapisi": rnd.choice(
                [
                    "подписан ЭЦП",
                    "подписан ЭЦП",
                    "подписан ЭЦП",
                    "черновик",
                ]
            ),
        }
        if rnd.random() < 0.07:
            duplicate = dict(visit)
            duplicate["id_priema"] = visit["id_priema"] + "_dup"
            duplicate["dt_priem"] = visit_date.strftime("%d.%m.%Y %H:%M")
            visits.append(duplicate)
        visits.append(visit)
    return visits
