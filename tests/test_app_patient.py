"""Tests for the Streamlit patient summary component."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.app.components import patient as component
from src.contracts.dashboard.v1 import (
    AllergySummary,
    ConditionSummary,
    DashboardPatient,
    DashboardResponse,
    MedicationSummary,
)


def test_patient_card_renders_profile_and_clinical_lists(
    monkeypatch,
) -> None:
    streamlit = MagicMock()
    metric_columns = [MagicMock() for _ in range(2)]
    streamlit.columns.return_value = metric_columns
    monkeypatch.setattr(component, "st", streamlit)

    component.render_patient_card(
        _dashboard(
            patient=DashboardPatient(
                id="patient-1",
                full_name="Иванов Иван Иванович",
                age=46,
                gender="male",
                blood_group="A(II) Rh+",
                bmi=27.84,
                last_weight_kg=90,
            ),
            allergies=[AllergySummary(agent="Пенициллин", reaction="сыпь")],
            conditions=[
                ConditionSummary(code="I10", display="Гипертензия", stage="II")
            ],
            current_medications=[
                MedicationSummary(
                    name="Препарат",
                    dose="10 мг",
                    frequency="1 раз в день",
                )
            ],
        )
    )

    streamlit.header.assert_called_once_with("Иванов Иван Иванович")
    streamlit.caption.assert_called_once_with("Краткая информация о пациенте")
    assert metric_columns[0].metric.call_args_list[0].args == ("Возраст", "46 лет")
    assert metric_columns[0].metric.call_args_list[1].args == ("Пол", "М")
    assert metric_columns[0].metric.call_args_list[2].args == (
        "Группа крови",
        "A(II) Rh+",
    )
    metric_columns[1].metric.assert_any_call("BMI", "27.8")
    metric_columns[1].metric.assert_any_call("Вес", "90.0 кг")
    streamlit.container.assert_called_once_with(border=True)
    assert streamlit.divider.call_count == 3
    streamlit.warning.assert_called_once_with("Пенициллин — сыпь")
    assert streamlit.subheader.call_args_list[1].args == (
        "Хронические заболевания",
    )
    assert "- Гипертензия (I10, II)" in _markdown_calls(streamlit)
    assert "- Препарат — 10 мг, 1 раз в день" in _markdown_calls(streamlit)


def test_patient_card_handles_missing_values_and_empty_lists(monkeypatch) -> None:
    streamlit = MagicMock()
    metric_columns = [MagicMock() for _ in range(2)]
    streamlit.columns.return_value = metric_columns
    monkeypatch.setattr(component, "st", streamlit)

    component.render_patient_card(
        _dashboard(patient=DashboardPatient(id="patient-1", full_name=""))
    )

    streamlit.header.assert_called_once_with("Имя пациента не указано")
    metric_values = [
        call.args[1]
        for column in metric_columns
        for call in column.metric.call_args_list
    ]
    assert metric_values == ["Нет данных"] * 5
    assert streamlit.info.call_args_list[0].args == (
        "Сведения об аллергиях отсутствуют.",
    )
    assert streamlit.info.call_args_list[1].args == (
        "Хронические состояния не указаны.",
    )
    assert streamlit.info.call_args_list[2].args == (
        "Текущая терапия не указана.",
    )
    streamlit.error.assert_not_called()
    streamlit.warning.assert_not_called()
    content_calls = [
        call.args[0]
        for call in streamlit.markdown.call_args_list
        if not call.kwargs.get("unsafe_allow_html")
    ]
    assert content_calls == []


def _dashboard(
    *,
    patient: DashboardPatient,
    allergies: list[AllergySummary] | None = None,
    conditions: list[ConditionSummary] | None = None,
    current_medications: list[MedicationSummary] | None = None,
) -> DashboardResponse:
    return DashboardResponse(
        generated_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
        patient=patient,
        allergies=allergies or [],
        conditions=conditions or [],
        current_medications=current_medications or [],
    )


def _markdown_calls(streamlit: MagicMock) -> list[str]:
    return [call.args[0] for call in streamlit.markdown.call_args_list]
