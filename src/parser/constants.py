"""Shared parser constants and output schemas."""

DEFAULT_OUTPUT_DIR = "data/processed/"

PROFILE_FIELDS = (
    "fio",
    "birth_date",
    "age",
    "gender",
    "blood_group",
    "bmi",
    "allergies",
    "chronic_diseases",
    "current_therapy",
)
VITALS_FIELDS = (
    "date",
    "sys_bp",
    "dia_bp",
    "heart_rate",
    "weight",
    "glucose",
    "hba1c",
    "creatinine",
    "cholesterol",
)
VISITS_FIELDS = ("date", "doctor", "specialty", "diagnosis", "complaints")

VITAL_BOUNDS: dict[str, tuple[float | None, float | None]] = {
    "sys_bp": (60, 300),
    "dia_bp": (30, 200),
    "heart_rate": (20, 250),
    "weight": (1, 500),
    "glucose": (0, 100),
    "hba1c": (0, 30),
    "creatinine": (0, 10_000),
    "cholesterol": (0, 100),
}

MISSING_STRINGS = {
    "",
    "-",
    "н/д",
    "нет данных",
    "null",
    "none",
    "nan",
}

RECORD_HINT_KEYS = {
    "id_priema",
    "visit_id",
    "dt_priem",
    "date",
    "vrach",
    "doctor",
    "diagnoz_priema",
    "diagnosis",
    "izmereniya",
    "measurements",
    "data_vzyatia",
    "rezultaty",
    "results",
    "pokazatel",
    "indicator",
    "dt",
    "izmereno",
    "sys",
    "dia",
    "pulse",
    "agent",
    "agent_name",
    "diagnoz_name",
    "preparat",
}
