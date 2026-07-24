"""Synthetic patient profile and longitudinal history sections."""

from __future__ import annotations

import random
from datetime import timedelta
from typing import Any

from .distortions import messy_date, messy_num, maybe_missing
from .models import GenerationWindow


def build_patient_sections(
    rnd: random.Random,
    window: GenerationWindow,
    years: int,
) -> dict[str, Any]:
    """Build profile blocks in their legacy random-call order."""

    start = window.start
    end = window.end
    patient_core = {
        "pat_id": "0004512-К",
        "FIO": "СИМАКОВ ВИКТОР ГЕННАДЬЕВИЧ",
        "pat_fam": "Симаков",
        "pat_im": "Виктор",
        "pat_otch": "Геннадьевич",
        "DATE_ROJD": "14.03.1967",
        "birht_date": "1967-03-14",
        "pol": maybe_missing("м", rnd, 0.0),
        "SEX_ID": 1,
        "snils_num": "112-233-445 95",
        "polis_OMS": {
            "ser": "",
            "num": "8277340871000512",
            "strah_org": "ООО СК «Согласие-М»",
        },
        "adres_reg": "г. Сочи, ул. Полтавская, д. 8, кв. 41",
        "strAdresFact": "тот же",
        "tel_mob": "+7 (9**) ***-**-12",
        "lgota_kod": maybe_missing("б/л", rnd, 0.5),
        "invalidnost": {"gruppa": None, "flag": 0, "prim": "-"},
        "blood_grp": "A(II) Rh+",
        "rost_sm": 176,
        "ves_kg_last": messy_num(96.5, rnd),
        "mesto_raboty": "ООО «ЮгСтройМонтаж», инженер-сметчик",
        "kem_napravlen": "самообращение",
    }

    social = {
        "VREDNYE_PRIVYCHKI": {
            "kurenie": {
                "status": "курит",
                "let_kurit": 31,
                "sigaret_v_den": messy_num(15, rnd),
                "indeks_kurilshika": "23,25 пачка/лет",
                "popytki_otkaza": 3,
                "comment": "с 2024 г. со слов сократил до 8-10 сиг/день",
            },
            "alkogol": {
                "status": "умеренно",
                "chastota": "1-2 раза в мес",
                "AUDIT_C": None,
            },
            "narkotiki": "отрицает",
            "fiz_aktivnost": "низкая, сидячая работа",
        },
        "allergoanamnez": [
            {
                "agent": "Пенициллин",
                "reakciya": "крапивница",
                "god_vyyavl": "1989",
                "tip": "лекарственная",
            },
            {
                "agent": "пыльца берёзы",
                "reakciya": "риноконъюнктивит",
                "god_vyyavl": None,
                "tip": "поллиноз",
            },
            {
                "AGENT_NAME": "Пенициллины (группа)",
                "react": "сыпь, зуд",
                "note": "дубль записи, перенос из бумажной карты",
            },
        ],
        "semeiny_anamnez": [
            {
                "rodstvo": "отец",
                "zabolevanie": "ИБС, инфаркт миокарда",
                "vozrast_debyuta": 52,
                "ishod": "умер в 61 год, повторный ИМ",
            },
            {
                "rodstvo": "мать",
                "zabolevanie": "СД 2 типа, артериальная гипертензия",
                "vozrast_debyuta": 58,
                "ishod": "жива",
            },
            {
                "rodstvo": "брат",
                "zabolevanie": "гипертоническая болезнь",
                "vozrast_debyuta": 45,
                "ishod": None,
            },
            {
                "rodstvo": "дед по отцу",
                "zabolevanie": "ОНМК",
                "vozrast_debyuta": "н/д",
                "ishod": "умер",
            },
        ],
        "professionalnye_vrednosti": (
            "работа за компьютером >8 ч, психоэмоциональное напряжение"
        ),
    }

    chronic = [
        {
            "MKB10_KOD": "I11.9",
            "DIAGNOZ_NAME": (
                "Гипертензивная болезнь сердца без сердечной недостаточности"
            ),
            "data_ustanovl": messy_date(
                start + timedelta(days=rnd.randint(0, 200)), rnd
            ),
            "stadia": "II ст., риск 4 (очень высокий)",
            "status": "хроническое",
            "dispanser_uchet": 1,
        },
        {
            "MKB10_KOD": "E11.9",
            "DIAGNOZ_NAME": "Сахарный диабет 2 типа",
            "data_ustanovl": messy_date(
                start + timedelta(days=int(365.25 * min(3, years - 1))),
                rnd,
            ),
            "stadia": "целевой HbA1c < 7%",
            "status": "хроническое",
            "dispanser_uchet": 1,
        },
        {
            "MKB10_KOD": "N18.3",
            "DIAGNOZ_NAME": "Хроническая болезнь почек, стадия 3а",
            "data_ustanovl": messy_date(
                start + timedelta(days=int(365.25 * min(5, years - 1))),
                rnd,
            ),
            "stadia": "С3а А2",
            "status": "хроническое",
            "dispanser_uchet": 1,
            "prim": "стадия пересмотрена: ранее С2",
        },
        {
            "MKB10_KOD": "E78.2",
            "DIAGNOZ_NAME": "Смешанная гиперлипидемия",
            "data_ustanovl": None,
            "stadia": "-",
            "status": "хроническое",
            "dispanser_uchet": 0,
        },
        {
            "MKB10_KOD": "I25.2",
            "DIAGNOZ_NAME": "Перенесённый в прошлом инфаркт миокарда",
            "data_ustanovl": "2019-11-08",
            "stadia": "ПИКС",
            "status": "анамнестическое",
            "dispanser_uchet": 1,
        },
        {
            "MKB10_KOD": "H36.0",
            "DIAGNOZ_NAME": (
                "Диабетическая ретинопатия, непролиферативная"
            ),
            "data_ustanovl": messy_date(end - timedelta(days=600), rnd),
            "stadia": "OU",
            "status": "хроническое",
            "dispanser_uchet": 0,
        },
    ]

    surgeries = [
        {
            "operaciya": "Аппендэктомия",
            "data": "1984 г.",
            "lpu": "ЦРБ г. Тихорецк",
            "oslojneniya": "без осложнений",
        },
        {
            "operaciya": "ЧКВ: стентирование ПКА (1 DES)",
            "data": "08.11.2019",
            "lpu": "ККБ №1 им. проф. С.В. Очаповского, г. Краснодар",
            "oslojneniya": None,
            "prim": "экстренно, по поводу ОИМ нижней стенки",
        },
        {
            "OPER_NAME": "Стентирование правой коронарной артерии",
            "DATA_OPER": "20191108",
            "note": "дубликат записи, импорт из выписки стационара",
        },
    ]

    hospitalizations = [
        {
            "lpu": "ККБ №1, кардиологическое отделение",
            "postuplenie": "08.11.2019",
            "vypiska": "19.11.2019",
            "diagnoz_zaklyuch": (
                "ОИМ с подъёмом ST нижней стенки ЛЖ от 08.11.2019. "
                "ЧКВ со стентированием ПКА."
            ),
            "MKB10": "I21.1",
            "ishod": "улучшение",
        },
        {
            "lpu": "ГБ №4, терапевтическое отделение",
            "postuplenie": messy_date(end - timedelta(days=430), rnd),
            "vypiska": messy_date(end - timedelta(days=421), rnd),
            "diagnoz_zaklyuch": (
                "Гипертонический криз, неосложнённый. ХБП С3а."
            ),
            "MKB10": "I10",
            "ishod": "улучшение",
        },
    ]

    vaccinations = [
        {
            "vakcina": "Грипп (Совигрипп)",
            "data": messy_date(
                end - timedelta(days=rnd.randint(180, 260)), rnd
            ),
            "seriya": "V-2210-08",
        },
        {
            "vakcina": "COVID-19 (ревакцинация)",
            "data": "2023-10-04",
            "seriya": None,
        },
        {"vakcina": "АДС-М", "data": "2017", "seriya": "-"},
    ]

    return {
        "PATIENT_INFO": patient_core,
        "social_anamnez": social,
        "hron_zabolevaniya": chronic,
        "perenesennye_operacii": surgeries,
        "gospitalizacii": hospitalizations,
        "privivki": vaccinations,
    }
