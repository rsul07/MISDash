"""Tests for the compact patient overview component."""

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


def test_patient_card_renders_compact_profile(monkeypatch) -> None:
    streamlit, card, stats, clinical = _streamlit()
    monkeypatch.setattr(component, "st", streamlit)
    section_header = MagicMock()
    monkeypatch.setattr(component, "render_section_header", section_header)

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

    section_header.assert_called_once()
    hero = card.columns.return_value[0].markdown.call_args.args[0]
    assert "Иванов Иван Иванович" in hero
    assert "ID · patient-1" in hero
    stat_html = [item.markdown.call_args.args[0] for item in stats]
    assert "Возраст" in stat_html[0] and "46 лет" in stat_html[0]
    assert "Пол" in stat_html[1] and ">М<" in stat_html[1]
    assert "Группа крови" in stat_html[2] and "A(II) Rh+" in stat_html[2]
    assert "BMI" in stat_html[3] and "27.8" in stat_html[3]
    assert "Вес" in stat_html[4] and "90.0 кг" in stat_html[4]


def test_patient_context_renders_three_clinical_panels(monkeypatch) -> None:
    streamlit, _, _, clinical = _streamlit()
    monkeypatch.setattr(component, "st", streamlit)
    monkeypatch.setattr(component, "render_section_header", MagicMock())

    component.render_patient_context(
        _dashboard(
            patient=DashboardPatient(id="patient-1", full_name="Пациент"),
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

    allergy_html = clinical[0].markdown.call_args.args[0]
    condition_html = clinical[1].markdown.call_args.args[0]
    medication_html = clinical[2].markdown.call_args.args[0]
    assert "Пенициллин" in allergy_html and "сыпь" in allergy_html
    assert "Гипертензия" in condition_html and "I10 · II" in condition_html
    assert "Препарат" in medication_html and "10 мг · 1 раз в день" in medication_html


def test_patient_card_escapes_values_and_handles_empty_lists(monkeypatch) -> None:
    streamlit, card, stats, clinical = _streamlit()
    monkeypatch.setattr(component, "st", streamlit)
    monkeypatch.setattr(component, "render_section_header", MagicMock())

    dashboard = _dashboard(
        patient=DashboardPatient(
            id="<patient>",
            full_name="<script>alert(1)</script>",
        )
    )
    component.render_patient_card(dashboard)
    component.render_patient_context(dashboard)

    hero = card.columns.return_value[0].markdown.call_args.args[0]
    assert "<script>" not in hero
    assert "&lt;script&gt;" in hero
    assert all("Нет данных" in item.markdown.call_args.args[0] for item in stats)
    assert all("Нет сведений" in item.markdown.call_args.args[0] for item in clinical)


def test_panel_helpers_escape_untrusted_clinical_text() -> None:
    html = component._allergies_html(
        [AllergySummary(agent="<b>agent</b>", reaction="<img>")]
    )

    assert "<b>agent</b>" not in html
    assert "&lt;b&gt;agent&lt;/b&gt;" in html
    assert "&lt;img&gt;" in html


def _streamlit() -> tuple[
    MagicMock,
    MagicMock,
    list[MagicMock],
    list[MagicMock],
]:
    streamlit = MagicMock()
    card = MagicMock()
    stats = [MagicMock() for _ in range(5)]
    hero_and_stats = [MagicMock(), *stats]
    clinical = [MagicMock() for _ in range(3)]
    card.columns.return_value = hero_and_stats
    streamlit.container.return_value = card
    streamlit.columns.return_value = clinical
    return streamlit, card, stats, clinical


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
