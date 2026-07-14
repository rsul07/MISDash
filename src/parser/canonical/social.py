"""Canonical social and family history adapter."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.contracts.patient.v1 import AlcoholUse, FamilyHistory, SocialHistory, TobaccoUse

from ..normalizers import clean_text, parse_number
from ..records import as_mapping, first, records
from .common import event_id, source_reference


@dataclass(frozen=True)
class SocialBundle:
    social_history: SocialHistory | None
    family_history: list[FamilyHistory]


def build_social_history(data: Mapping[str, Any]) -> SocialBundle:
    social = as_mapping(
        first(data, "social_anamnez", "social_history", "social_anamnesis")
    )
    if not social:
        return SocialBundle(social_history=None, family_history=[])
    habits = as_mapping(
        first(social, "VREDNYE_PRIVYCHKI", "habits", "lifestyle")
    )
    family = _build_family_history(
        first(social, "semeiny_anamnez", "family_history")
    )
    history = SocialHistory(
        source=source_reference("social_anamnez"),
        tobacco=_tobacco(first(habits, "kurenie", "smoking", "tobacco")),
        alcohol=_alcohol(first(habits, "alkogol", "alcohol")),
        substance_use=clean_text(
            first(habits, "narkotiki", "substance_use", "drugs")
        )
        or None,
        physical_activity=clean_text(
            first(habits, "fiz_aktivnost", "physical_activity")
        )
        or None,
        occupational_hazards=clean_text(
            first(
                social,
                "professionalnye_vrednosti",
                "occupational_hazards",
            )
        )
        or None,
    )
    has_lifestyle = any(
        (
            history.tobacco,
            history.alcohol,
            history.substance_use,
            history.physical_activity,
            history.occupational_hazards,
        )
    )
    return SocialBundle(
        social_history=history if has_lifestyle else None,
        family_history=family,
    )


def _tobacco(source: Any) -> TobaccoUse | None:
    item = as_mapping(source)
    if not item:
        text = clean_text(source)
        return TobaccoUse(status=text) if text else None
    pack_years_text = clean_text(
        first(item, "indeks_kurilshika", "pack_years", "smoking_index")
    )
    return TobaccoUse(
        status=clean_text(first(item, "status")) or None,
        years=parse_number(first(item, "let_kurit", "years")),
        cigarettes_per_day=parse_number(
            first(item, "sigaret_v_den", "cigarettes_per_day")
        ),
        pack_years=_number_from_text(pack_years_text),
        pack_years_text=pack_years_text or None,
        quit_attempts=_integer(first(item, "popytki_otkaza", "quit_attempts")),
        note=clean_text(first(item, "comment", "note")) or None,
    )


def _alcohol(source: Any) -> AlcoholUse | None:
    item = as_mapping(source)
    if not item:
        text = clean_text(source)
        return AlcoholUse(status=text) if text else None
    return AlcoholUse(
        status=clean_text(first(item, "status")) or None,
        frequency=clean_text(first(item, "chastota", "frequency")) or None,
        audit_c_score=parse_number(first(item, "AUDIT_C", "audit_c_score")),
    )


def _build_family_history(source: Any) -> list[FamilyHistory]:
    result: list[FamilyHistory] = []
    for index, item in enumerate(records(source)):
        condition = clean_text(
            first(item, "zabolevanie", "condition", "diagnosis")
        )
        if not condition:
            continue
        source_id = first(item, "id", "family_history_id")
        result.append(
            FamilyHistory(
                id=event_id("family-history", index, source_id),
                source=source_reference("social_anamnez.semeiny_anamnez", index, source_id),
                relationship=clean_text(first(item, "rodstvo", "relationship"))
                or None,
                condition=condition,
                onset_age=parse_number(
                    first(item, "vozrast_debyuta", "onset_age", "age")
                ),
                outcome=clean_text(first(item, "ishod", "outcome")) or None,
            )
        )
    return result


def _number_from_text(value: str) -> float | None:
    match = re.search(r"[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)", value)
    return parse_number(match.group(0)) if match else None


def _integer(value: Any) -> int | None:
    number = parse_number(value)
    return int(number) if number is not None else None
