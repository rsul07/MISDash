"""Compact patient overview rendered from DashboardResponse v1."""

from __future__ import annotations

from html import escape

import streamlit as st

from src.app.theme import render_section_header
from src.contracts.dashboard.v1 import (
    AllergySummary,
    ConditionSummary,
    DashboardResponse,
    MedicationSummary,
)


_GENDER_LABELS = {
    "female": "Ж",
    "male": "М",
}
_MISSING = "Нет данных"


def render_patient_card(dashboard: DashboardResponse) -> None:
    """Render the patient hero and three concise clinical collections."""

    patient = dashboard.patient
    render_section_header(
        "Пациент",
        eyebrow="ОБЗОР",
        description="Ключевые сведения из нормализованной медицинской истории.",
    )

    card = st.container(border=True)
    card.markdown(
        (
            '<span class="mis-patient-marker"></span>'
            '<div class="mis-patient-heading mis-enter">'
            f'<div class="mis-patient-id">ID · {escape(patient.id)}</div>'
            f"<h2>{escape(patient.full_name or 'Имя пациента не указано')}</h2>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    stats = card.columns(5, gap="small")
    stats[0].metric("Возраст", _format_age(patient.age))
    stats[1].metric("Пол", _format_gender(patient.gender))
    stats[2].metric("Группа крови", patient.blood_group or _MISSING)
    stats[3].metric("BMI", _format_number(patient.bmi))
    stats[4].metric("Вес", _format_weight(patient.last_weight_kg))

    clinical = card.columns((1, 1.35, 1.65), gap="medium")
    clinical[0].markdown(
        _allergies_html(dashboard.allergies),
        unsafe_allow_html=True,
    )
    clinical[1].markdown(
        _conditions_html(dashboard.conditions),
        unsafe_allow_html=True,
    )
    clinical[2].markdown(
        _medications_html(dashboard.current_medications),
        unsafe_allow_html=True,
    )


def _allergies_html(allergies: list[AllergySummary]) -> str:
    if not allergies:
        content = '<div class="mis-empty-copy">Нет сведений</div>'
    else:
        content = "".join(
            (
                '<div class="mis-clinical-item mis-allergy-item">'
                f"<strong>{escape(item.agent)}</strong>"
                f"<span>{escape(item.reaction or 'Реакция не указана')}</span>"
                "</div>"
            )
            for item in allergies
        )
    return _clinical_panel("Аллергии", len(allergies), content)


def _conditions_html(conditions: list[ConditionSummary]) -> str:
    if not conditions:
        content = '<div class="mis-empty-copy">Нет сведений</div>'
    else:
        content = "".join(_condition_html(item) for item in conditions)
    return _clinical_panel("Диагнозы", len(conditions), content)


def _condition_html(condition: ConditionSummary) -> str:
    details = " · ".join(
        escape(value)
        for value in (
            condition.code,
            condition.stage,
            condition.clinical_status,
        )
        if value
    )
    metadata = f"<span>{details}</span>" if details else ""
    return (
        '<div class="mis-clinical-item">'
        f"<strong>{escape(condition.display)}</strong>"
        f"{metadata}"
        "</div>"
    )


def _medications_html(medications: list[MedicationSummary]) -> str:
    if not medications:
        content = '<div class="mis-empty-copy">Нет сведений</div>'
    else:
        content = "".join(_medication_html(item) for item in medications)
    return _clinical_panel("Текущая терапия", len(medications), content)


def _medication_html(medication: MedicationSummary) -> str:
    details = " · ".join(
        escape(value)
        for value in (
            medication.dose,
            medication.frequency,
            medication.form,
        )
        if value
    )
    metadata = f"<span>{details}</span>" if details else ""
    return (
        '<div class="mis-clinical-item">'
        f"<strong>{escape(medication.name)}</strong>"
        f"{metadata}"
        "</div>"
    )


def _clinical_panel(title: str, count: int, content: str) -> str:
    return (
        '<section class="mis-clinical-panel">'
        '<div class="mis-clinical-title">'
        f"<h3>{escape(title)}</h3>"
        f"<span>{count}</span>"
        "</div>"
        f'<div class="mis-clinical-list">{content}</div>'
        "</section>"
    )


def _format_age(value: int | None) -> str:
    return f"{value} лет" if value is not None else _MISSING


def _format_gender(value: str | None) -> str:
    if value is None:
        return _MISSING
    return _GENDER_LABELS.get(value.casefold(), value)


def _format_number(value: float | None) -> str:
    return f"{value:.1f}" if value is not None else _MISSING


def _format_weight(value: float | None) -> str:
    return f"{value:.1f} кг" if value is not None else _MISSING
