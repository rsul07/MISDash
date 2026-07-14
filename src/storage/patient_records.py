"""Read and atomically write PatientRecord JSON documents."""

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


def save_patient_record(path: str | Path, record: PatientRecord) -> Path:
    target_path = Path(path).expanduser()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = target_path.with_suffix(f"{target_path.suffix}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8") as target:
            json.dump(
                record.model_dump(mode="json"),
                target,
                ensure_ascii=False,
                indent=2,
            )
            target.write("\n")
        temporary_path.replace(target_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return target_path
