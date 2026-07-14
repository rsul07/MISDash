"""Encounter timeline projection for DashboardResponse v1."""

from src.contracts.dashboard.v1 import CodeLabel, VisitSummary
from src.contracts.patient.v1 import PatientRecord

from .common import chronological_key


def build_visit_summaries(record: PatientRecord) -> list[VisitSummary]:
    visits = [
        VisitSummary(
            id=item.id,
            occurred_at=item.occurred_at,
            practitioner=item.practitioner.name,
            specialty=item.practitioner.specialty,
            encounter_type=item.encounter_type,
            diagnoses=[
                CodeLabel(code=diagnosis.coding.code, display=diagnosis.coding.display)
                for diagnosis in item.diagnoses
            ],
            complaints=item.complaints,
        )
        for item in record.encounters
    ]
    visits.sort(
        key=lambda item: chronological_key(item.occurred_at),
        reverse=True,
    )
    return visits
