"""Canonical observations collected from every supported MIS source."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.contracts.patient.v1 import DiagnosticReport, Observation

from .diary import build_diary_observations
from .direct import build_direct_observations
from .laboratory import LaboratoryBundle, build_laboratory
from .visits import build_visit_observations


@dataclass(frozen=True)
class ObservationBundle:
    observations: list[Observation]
    diagnostic_reports: list[DiagnosticReport]


def build_observations(data: Mapping[str, Any]) -> ObservationBundle:
    laboratory: LaboratoryBundle = build_laboratory(data)
    return ObservationBundle(
        observations=[
            *build_diary_observations(data),
            *build_direct_observations(data),
            *laboratory.observations,
            *build_visit_observations(data),
        ],
        diagnostic_reports=laboratory.reports,
    )


__all__ = ["ObservationBundle", "build_observations"]
