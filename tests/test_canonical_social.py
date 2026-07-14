"""Tests for canonical social and family history."""

from __future__ import annotations

import json
from pathlib import Path

from src.parser.canonical.social import build_social_history


def test_social_adapter_preserves_lifestyle_and_family_history() -> None:
    bundle = build_social_history(_etalon_data())

    assert bundle.social_history is not None
    assert bundle.social_history.tobacco is not None
    assert bundle.social_history.tobacco.status == "курит"
    assert bundle.social_history.tobacco.years == 31
    assert bundle.social_history.tobacco.cigarettes_per_day == 15
    assert bundle.social_history.tobacco.pack_years == 23.25
    assert bundle.social_history.tobacco.pack_years_text == "23,25 пачка/лет"
    assert bundle.social_history.alcohol is not None
    assert bundle.social_history.alcohol.frequency == "1-2 раза в мес"
    assert bundle.social_history.physical_activity == "низкая, сидячая работа"
    assert bundle.social_history.occupational_hazards
    assert len(bundle.family_history) == 4
    assert bundle.family_history[0].relationship == "отец"
    assert bundle.family_history[0].onset_age == 52


def test_social_adapter_tolerates_missing_and_text_habits() -> None:
    assert build_social_history({}).social_history is None

    bundle = build_social_history(
        {
            "social_anamnez": {
                "VREDNYE_PRIVYCHKI": {
                    "kurenie": "не курит",
                    "alkogol": "не употребляет",
                },
                "semeiny_anamnez": "wrong",
            }
        }
    )

    assert bundle.social_history is not None
    assert bundle.social_history.tobacco is not None
    assert bundle.social_history.tobacco.status == "не курит"
    assert bundle.social_history.alcohol is not None
    assert bundle.family_history == []


def _etalon_data() -> dict[str, object]:
    path = Path(__file__).parents[1] / "data" / "patient_etalon.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("data", payload)
