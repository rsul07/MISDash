"""Patient summary card rendered from DashboardResponse v1."""

from __future__ import annotations

import streamlit as st

from src.contracts.dashboard.v1 import DashboardResponse


_GENDER_LABELS = {
    "female": "Женский",
    "male": "Мужской",
}
_MISSING = "Нет данных"


def render_patient_card(dashboard: DashboardResponse) -> None:
    """Render the patient header and clinical summary collections."""

    patient = dashboard.patient
    st.header(patient.full_name or "Имя пациента не указано")

    age, gender, blood_group, bmi, weight = st.columns(5)
    age.metric("Возраст", _format_age(patient.age))
    gender.metric("Пол", _format_gender(patient.gender))
    blood_group.metric("Группа крови", patient.blood_group or _MISSING)
    bmi.metric("BMI", _format_number(patient.bmi))
    weight.metric("Вес", _format_weight(patient.last_weight_kg))

    st.subheader("Аллергии")
    if dashboard.allergies:
        for allergy in dashboard.allergies:
            reaction = f" — {allergy.reaction}" if allergy.reaction else ""
            st.error(f"{allergy.agent}{reaction}")
    else:
        st.info("Сведения об аллергиях отсутствуют.")

    st.subheader("Хронические состояния")
    if dashboard.conditions:
        for condition in dashboard.conditions:
            details = [condition.code, condition.stage, condition.clinical_status]
            suffix = ", ".join(item for item in details if item)
            label = f"{condition.display} ({suffix})" if suffix else condition.display
            st.markdown(f"- {label}")
    else:
        st.info("Хронические состояния не указаны.")

    st.subheader("Текущая терапия")
    if dashboard.current_medications:
        for medication in dashboard.current_medications:
            details = [medication.dose, medication.frequency, medication.form]
            suffix = ", ".join(item for item in details if item)
            label = f"{medication.name} — {suffix}" if suffix else medication.name
            st.markdown(f"- {label}")
    else:
        st.info("Текущая терапия не указана.")


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
