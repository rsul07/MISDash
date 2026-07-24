"""Top-level composition of one dirty synthetic MIS payload."""

from __future__ import annotations

import random
from typing import Any

from .diaries import build_diaries
from .encounters import build_encounters
from .investigations import build_instrumental, build_laboratory
from .metadata import build_metadata
from .models import GenerationConfig, GenerationWindow
from .patient import build_patient_sections


def build_export(
    rnd: random.Random,
    config: GenerationConfig,
) -> dict[str, Any]:
    """Build all sections while preserving the legacy RNG sequence."""

    window = GenerationWindow.from_years(config.years)
    sections = build_patient_sections(rnd, window, config.years)
    visits = build_encounters(
        rnd, window, config.years, config.light
    )
    labs = build_laboratory(rnd, window, config.years, config.light)
    instrumental = build_instrumental(
        rnd, window, config.years, config.light
    )
    diaries = build_diaries(rnd, window, config.years)
    events, legacy, service_noise = build_metadata(
        rnd, window.end, visits, labs, instrumental
    )

    return {
        "result": {
            "code": 0,
            "msg": "OK",
            "req_id": "a41c9f00-3e2b-4bd1-9c77-demo",
        },
        "data": {
            **sections,
            "PRIEMY_VRACHA": visits,
            "lab_issledovaniya": labs,
            "instrumental_issled": instrumental,
            "dnevnik_samokontrolya": diaries,
            "EHR_EVENT_LOG": events,
            "legacy_import_v3": legacy,
            "sluzhebnoe": service_noise,
        },
    }
