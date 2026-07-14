"""Backend projections built from versioned canonical records."""

from .dashboard import DashboardService
from .repository import load_patient_record

__all__ = ["DashboardService", "load_patient_record"]
