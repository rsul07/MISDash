"""Synthetic laboratory and instrumental investigation sections."""

from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

from .catalogs import INSTRUMENTAL, LAB_PANELS, PANEL_KEY_STYLES
from .distortions import messy_date, messy_num, maybe_missing
from .models import GenerationWindow


def build_laboratory(
    rnd: random.Random,
    window: GenerationWindow,
    years: int,
    light: bool,
) -> list[dict[str, Any]]:
    labs: list[dict[str, Any]] = []
    laboratory_id = 700000
    count = years * 78 if not light else years * 8
    days = sorted(
        window.start
        + timedelta(days=rnd.randint(0, int(years * 365.25)))
        for _ in range(count)
    )
    for laboratory_date in days:
        fraction = window.fraction(laboratory_date)
        chosen = rnd.sample(
            list(LAB_PANELS.keys()), k=rnd.randint(1, 3)
        )
        for panel in chosen:
            laboratory_id += rnd.randint(1, 9)
            rows: list[dict[str, Any]] = []
            for name, unit, low, high, base, drift in LAB_PANELS[panel]:
                value = (
                    base
                    + drift * years * fraction
                    + rnd.gauss(
                        0,
                        (high - low) * 0.05
                        if high > low
                        else base * 0.05,
                    )
                )
                value = round(max(value, 0), 2)
                flag = ""
                if high > low:
                    if value > high:
                        flag = "H"
                    elif value < low:
                        flag = "L"
                row = {
                    "pokazatel": name,
                    "REZULT": messy_num(value, rnd),
                    "ed_izm": maybe_missing(unit, rnd, 0.08),
                    "referens": maybe_missing(
                        f"{low} - {high}".replace(".", ","), rnd, 0.12
                    ),
                    "flag_H_L": flag,
                    "metod": maybe_missing(
                        rnd.choice(
                            [
                                "фотометрия",
                                "ИФА",
                                "автоматический анализатор",
                                "-",
                            ]
                        ),
                        rnd,
                        0.4,
                    ),
                }
                if rnd.random() < 0.05:
                    row["comment_lab"] = rnd.choice(
                        [
                            "гемолиз, интерпретировать с осторожностью",
                            "повторное исследование",
                            "хилёз",
                        ]
                    )
                row.update(
                    {
                        "id_pokazatelya": rnd.randint(10_000, 99_999),
                        "kod_nsi": (
                            f"NSI.{rnd.randint(1, 60)}."
                            f"{rnd.randint(100, 999)}"
                        ),
                        "sort_order": len(rows) + 1,
                        "status_rez": rnd.choice(
                            ["final", "final", "final", "corrected"]
                        ),
                        "dt_validacii": messy_date(
                            laboratory_date
                            + timedelta(
                                days=rnd.randint(0, 2),
                                hours=rnd.randint(8, 19),
                            ),
                            rnd,
                        ),
                        "is_deleted": 0,
                        "vneshniy_kod": maybe_missing(
                            f"L-{rnd.randint(1000, 9999)}", rnd, 0.25
                        ),
                    }
                )
                rows.append(row)
            labs.append(
                {
                    "nomer_zakaza": f"LB{laboratory_id}",
                    "data_vzyatia": messy_date(laboratory_date, rnd),
                    "data_gotovnosti": messy_date(
                        laboratory_date
                        + timedelta(days=rnd.randint(0, 2)),
                        rnd,
                    ),
                    "gruppa_issled": PANEL_KEY_STYLES[panel],
                    "gruppa_issled_name": panel,
                    "biomaterial": (
                        "моча"
                        if "мочи" in panel
                        or panel in ("ОАМ", "Микроальбуминурия")
                        else "кровь венозная"
                    ),
                    "lab_otdelenie": rnd.choice(
                        [
                            "КДЛ поликлиники",
                            "ЦКДЛ",
                            "внешняя лаборатория «ИнВитроЛаб»",
                        ]
                    ),
                    "REZULTATY": rows,
                    "vrach_kdl": rnd.choice(
                        ["Осипова Н.Н.", "Тер-Аванесова К.Г.", None]
                    ),
                }
            )
    return labs


def build_instrumental(
    rnd: random.Random,
    window: GenerationWindow,
    years: int,
    light: bool,
) -> list[dict[str, Any]]:
    instrumental: list[dict[str, Any]] = []
    count = years * 4 if not light else years
    for _ in range(count):
        investigation_date = window.start + timedelta(
            days=rnd.randint(0, int(years * 365.25))
        )
        fraction = window.fraction(investigation_date)
        kind, template, extras = rnd.choice(INSTRUMENTAL)
        text = template.format(
            hr=rnd.randint(58, 88),
            ef=rnd.randint(48, 55),
            mgp=rnd.randint(12, 14),
            zslg=rnd.randint(11, 13),
            rk1=rnd.randint(98, 110),
            rk2=rnd.randint(45, 55),
            lk1=rnd.randint(97, 108),
            lk2=rnd.randint(44, 54),
            par=round(17 - 3 * fraction + rnd.random(), 1),
            sten=rnd.randint(35, 55),
            lpi1=str(round(0.85 - 0.1 * fraction, 2)).replace(
                ".", ","
            ),
            lpi2=str(round(0.95 - 0.08 * fraction, 2)).replace(
                ".", ","
            ),
            sys=int(145 + 15 * fraction),
            dia=int(88 + 5 * fraction),
            it=rnd.randint(45, 78),
            extra=rnd.choice(extras) if extras else "",
        ).strip()
        instrumental.append(
            {
                "issledovanie": kind,
                "DT_ISSLED": messy_date(investigation_date, rnd),
                "zakluchenie_txt": text,
                "apparat": maybe_missing(
                    rnd.choice(
                        [
                            "GE Vivid S70",
                            "Schiller AT-102",
                            "Mindray DC-70",
                            "-",
                        ]
                    ),
                    rnd,
                    0.3,
                ),
                "vrach_fd": rnd.choice(
                    ["Кан Е.Ю.", "Стрельникова А.А.", "Мовсесян Г.А."]
                ),
                "protokol_id": f"FD-{rnd.randint(10000, 99999)}",
            }
        )
    return instrumental
