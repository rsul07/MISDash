"""Shared value objects for DashboardResponse v1."""

from src.contracts.patient.v1.common import ContractModel


class CodeLabel(ContractModel):
    code: str | None = None
    display: str
