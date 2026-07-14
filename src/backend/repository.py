"""Storage boundary for canonical PatientRecord JSON documents."""

from __future__ import annotations

import json
from pathlib import Path

from src.contracts.v1 import PatientRecord


def load_patient_record(path: str | Path) -> PatientRecord:
    source_path = Path(path).expanduser()
    try:
        with source_path.open(encoding="utf-8-sig") as source:
            payload = json.load(source)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid PatientRecord JSON in {source_path}: {error.msg}"
        ) from error
    return PatientRecord.model_validate(payload)
