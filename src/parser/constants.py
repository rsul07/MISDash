"""Shared constants for tolerant MIS parsing."""

DEFAULT_OUTPUT_DIR = "data/processed/"

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
