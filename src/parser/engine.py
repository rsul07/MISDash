"""Public orchestration facade for the MIS parser package."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.contracts.v1 import PatientRecord
from src.storage import save_patient_record

from .canonical.builder import build_patient_record
from .constants import DEFAULT_OUTPUT_DIR
from .extractors import extract_vitals_from_text
from .normalizers import (
    normalize_date,
    normalize_number,
    parse_date,
    parse_number,
)
from .records import as_mapping, first


class MISParser:
    """Parse one dirty MIS JSON export into PatientRecord v1."""

    normalize_date = staticmethod(normalize_date)
    parse_date = staticmethod(parse_date)
    parse_number = staticmethod(parse_number)
    normalize_number = staticmethod(normalize_number)
    extract_vitals_from_text = staticmethod(extract_vitals_from_text)

    def __init__(
        self,
        input_path: str | os.PathLike[str],
        output_dir: str | os.PathLike[str] | None = None,
    ) -> None:
        self.input_path = Path(input_path).expanduser()
        configured_output = (
            output_dir
            if output_dir is not None
            else os.getenv("OUTPUT_DIR") or DEFAULT_OUTPUT_DIR
        )
        self.output_dir = Path(configured_output).expanduser()

    def parse(self) -> dict[str, Path]:
        """Parse and persist the canonical record, returning its path."""

        patient_record = self.parse_record()
        path = self.output_dir / "patient_record.json"
        save_patient_record(path, patient_record)
        return {"patient_record": path}

    def parse_record(self) -> PatientRecord:
        """Parse the input without filesystem output."""

        data = self._medical_data(self._load_json())
        return build_patient_record(data)

    def run(self) -> dict[str, Path]:
        """Alias for :meth:`parse` for command-style callers."""

        return self.parse()

    def _load_json(self) -> Any:
        try:
            with self.input_path.open(encoding="utf-8-sig") as source:
                return json.load(source)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in {self.input_path}: {error.msg}") from error

    @staticmethod
    def _medical_data(payload: Any) -> Mapping[str, Any]:
        root = as_mapping(payload)
        nested = first(root, "data")
        return as_mapping(nested) if isinstance(nested, Mapping) else root

__all__ = [
    "MISParser",
    "extract_vitals_from_text",
    "normalize_date",
    "normalize_number",
    "parse_date",
    "parse_number",
]
