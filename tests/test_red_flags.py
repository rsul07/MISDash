"""Executable specification for the deterministic red-flag engine."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.contracts.dashboard.v1 import MetricPoint, MetricSeries
from src.contracts.patient.v1 import Condition, Encounter, Patient, PatientRecord
from src.contracts.patient.v1.common import Coding, SourceReference
from src.red_flags import evaluate_red_flags
from src.red_flags.common import format_observed_at


SOURCE = SourceReference(block="test")
AS_OF = date(2026, 7, 24)


def test_empty_record_has_no_red_flags() -> None:
    assert evaluate_red_flags(_record(), [], as_of=AS_OF) == []


def test_midnight_datetime_is_formatted_as_a_clinical_date() -> None:
    assert format_observed_at(datetime(2026, 7, 1)) == "01.07.2026"
    assert format_observed_at(datetime(2026, 7, 1, 12, 30)) == (
        "01.07.2026 12:30"
    )


@pytest.mark.parametrize(
    ("value", "expected_severity"),
    [(5.5, None), (5.51, "warning"), (6.0, "warning"), (6.5, "critical")],
)
def test_potassium_thresholds(
    value: float,
    expected_severity: str | None,
) -> None:
    flags = evaluate_red_flags(
        _record(),
        [_series("potassium", value, unit="mmol/L")],
        as_of=AS_OF,
    )

    if expected_severity is None:
        assert flags == []
    else:
        assert flags[0].code == "latest-potassium-above-5-5"
        assert flags[0].severity == expected_severity
        assert f"{value:g}" in flags[0].explanation


def test_hba1c_rule_uses_latest_value_across_date_types() -> None:
    series = _series("hba1c", 9.1, unit="%")
    series.points.insert(
        0,
        _point(
            11.0,
            source_id="older",
            observed_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ),
    )

    flags = evaluate_red_flags(_record(), [series], as_of=AS_OF)

    assert [flag.code for flag in flags] == ["latest-hba1c-above-8"]
    assert "9.1%" in flags[0].explanation


@pytest.mark.parametrize(
    ("value", "expected_severity"),
    [(45.0, None), (44.9, "warning"), (29.9, "critical")],
)
def test_egfr_thresholds(
    value: float,
    expected_severity: str | None,
) -> None:
    flags = evaluate_red_flags(
        _record(),
        [_series("egfr-ckd-epi-2021", value, unit="mL/min/1.73m2")],
        as_of=AS_OF,
    )

    if expected_severity is None:
        assert flags == []
    else:
        assert flags[0].code == "latest-egfr-below-45"
        assert flags[0].severity == expected_severity


def test_ldl_target_is_only_applied_with_documented_ascvd() -> None:
    ldl = [_series("ldl-cholesterol", 2.2, unit="mmol/L")]

    without_ascvd = evaluate_red_flags(_record(), ldl, as_of=AS_OF)
    with_ascvd = evaluate_red_flags(
        _record(
            conditions=[
                Condition(
                    id="condition-mi",
                    source=SOURCE,
                    coding=Coding(
                        code="I25.2",
                        display="Перенесённый инфаркт миокарда",
                    ),
                )
            ]
        ),
        ldl,
        as_of=AS_OF,
    )

    assert without_ascvd == []
    assert with_ascvd[0].code == "latest-ldl-above-ascvd-target"
    assert "2.2 mmol/L" in with_ascvd[0].explanation


def test_blood_pressure_requires_a_pair_from_one_source_event() -> None:
    unpaired = [
        _series("systolic", 190, source_id="bp-a", unit="mmHg"),
        _series("diastolic", 125, source_id="bp-b", unit="mmHg"),
    ]
    paired = [
        _series("systolic", 190, source_id="bp-a", unit="mmHg"),
        _series("diastolic", 90, source_id="bp-a", unit="mmHg"),
    ]

    assert evaluate_red_flags(_record(), unpaired, as_of=AS_OF) == []
    flags = evaluate_red_flags(_record(), paired, as_of=AS_OF)

    assert flags[0].code == "latest-blood-pressure-markedly-high"
    assert flags[0].severity == "critical"
    assert "190/90 mmHg" in flags[0].explanation
    assert "не устанавливает гипертонический криз" in flags[0].explanation


def test_diabetes_follow_up_rule_uses_last_ophthalmology_encounter() -> None:
    record = _record(
        conditions=[
            Condition(
                id="diabetes",
                source=SOURCE,
                coding=Coding(code="E11.9", display="Сахарный диабет 2 типа"),
            )
        ],
        encounters=[
            Encounter(
                id="eye-visit",
                source=SOURCE,
                occurred_at=date(2024, 7, 24),
                practitioner={"specialty": "офтальмолог"},
            )
        ],
    )

    flags = evaluate_red_flags(record, [], as_of=AS_OF)

    assert flags[0].code == "diabetes-ophthalmology-follow-up-gap"
    assert "24.07.2024" in flags[0].explanation
    assert "полноту выгрузки" in flags[0].explanation


def test_recent_ophthalmology_encounter_suppresses_follow_up_flag() -> None:
    record = _record(
        conditions=[
            Condition(
                id="diabetes",
                source=SOURCE,
                coding=Coding(code="E11", display="Диабет"),
            )
        ],
        encounters=[
            Encounter(
                id="eye-visit",
                source=SOURCE,
                occurred_at=date(2025, 7, 25),
                practitioner={"specialty": "врач-офтальмолог"},
            )
        ],
    )

    assert evaluate_red_flags(record, [], as_of=AS_OF) == []


def test_retinopathy_requires_annual_ophthalmology_follow_up() -> None:
    record = _record(
        conditions=[
            Condition(
                id="diabetes",
                source=SOURCE,
                coding=Coding(code="E11", display="Диабет"),
            ),
            Condition(
                id="retinopathy",
                source=SOURCE,
                coding=Coding(code="H36.0", display="Диабетическая ретинопатия"),
            ),
        ],
        encounters=[
            Encounter(
                id="eye-visit",
                source=SOURCE,
                occurred_at=date(2025, 7, 24),
                practitioner={"specialty": "офтальмолог"},
            )
        ],
    )

    flags = evaluate_red_flags(record, [], as_of=AS_OF)

    assert flags[0].code == "diabetes-ophthalmology-follow-up-gap"
    assert "не менее 1 года" in flags[0].explanation


def test_flags_are_sorted_by_severity_then_stable_code() -> None:
    flags = evaluate_red_flags(
        _record(),
        [
            _series("hba1c", 9.0, unit="%"),
            _series("potassium", 6.5, unit="mmol/L"),
        ],
        as_of=AS_OF,
    )

    assert [flag.severity for flag in flags] == ["critical", "warning"]


def _record(
    *,
    conditions: list[Condition] | None = None,
    encounters: list[Encounter] | None = None,
) -> PatientRecord:
    return PatientRecord(
        patient=Patient(
            id="patient-1",
            full_name="Тестовый пациент",
            source=SOURCE,
        ),
        conditions=conditions or [],
        encounters=encounters or [],
    )


def _series(
    code: str,
    value: float,
    *,
    source_id: str = "observation-1",
    unit: str,
) -> MetricSeries:
    return MetricSeries(
        code=code,
        display=code,
        unit=unit,
        points=[_point(value, source_id=source_id)],
    )


def _point(
    value: float,
    *,
    source_id: str,
    observed_at: date | datetime = date(2026, 7, 1),
) -> MetricPoint:
    return MetricPoint(
        observed_at=observed_at,
        value=value,
        source_category="laboratory",
        source_ids=[source_id],
    )
