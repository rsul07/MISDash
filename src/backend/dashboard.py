"""Application service that builds DashboardResponse v1."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from src.contracts.dashboard.v1 import DashboardResponse
from src.contracts.v1 import PatientRecord

from .metrics import build_metric_series
from .profile import build_profile_projection
from .repository import load_patient_record
from .visits import build_visit_summaries


class DashboardService:
    """Build stable frontend projections from canonical patient records."""

    def build(
        self,
        record: PatientRecord,
        *,
        as_of: date | None = None,
        generated_at: datetime | None = None,
    ) -> DashboardResponse:
        generated_at = generated_at or datetime.now(timezone.utc)
        as_of = as_of or generated_at.date()
        profile = build_profile_projection(record, as_of=as_of)
        return DashboardResponse(
            generated_at=generated_at,
            patient=profile.patient,
            allergies=profile.allergies,
            conditions=profile.conditions,
            current_medications=profile.current_medications,
            metrics=build_metric_series(record),
            visits=build_visit_summaries(record),
        )

    def build_from_path(
        self,
        path: str | Path,
        *,
        as_of: date | None = None,
        generated_at: datetime | None = None,
    ) -> DashboardResponse:
        return self.build(
            load_patient_record(path),
            as_of=as_of,
            generated_at=generated_at,
        )
