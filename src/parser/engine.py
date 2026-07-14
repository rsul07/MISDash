"""Public orchestration facade for the MIS parser package."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .constants import (
    DEFAULT_OUTPUT_DIR,
    PROFILE_FIELDS,
    VISITS_FIELDS,
    VITALS_FIELDS,
)
from .extractors import extract_vitals_from_text
from .normalizers import (
    normalize_date,
    normalize_number,
    parse_date,
    parse_number,
)
from .profile import build_profile
from .records import as_mapping, first
from .visits import build_visits
from .vitals import build_vitals
from .writers import write_csv, write_profile


class MISParser:
    """Parse one MIS JSON export and save dashboard-ready data files."""

    profile_fields = PROFILE_FIELDS
    vitals_fields = VITALS_FIELDS
    visits_fields = VISITS_FIELDS
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
        """Parse the input and return paths of the generated contract files."""

        data = self._medical_data(self._load_json())
        profile = build_profile(data)
        visits = build_visits(data)
        vitals = build_vitals(data)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "profile": self.output_dir / "profile.json",
            "vitals": self.output_dir / "vitals.csv",
            "visits": self.output_dir / "visits.csv",
        }
        write_profile(paths["profile"], profile)
        write_csv(paths["vitals"], VITALS_FIELDS, vitals)
        write_csv(paths["visits"], VISITS_FIELDS, visits)
        return paths

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

    # Compatibility wrappers for integrations that used these private methods.
    _build_profile = staticmethod(build_profile)
    _build_visits = staticmethod(build_visits)
    _build_vitals = staticmethod(build_vitals)


__all__ = [
    "MISParser",
    "PROFILE_FIELDS",
    "VITALS_FIELDS",
    "VISITS_FIELDS",
    "extract_vitals_from_text",
    "normalize_date",
    "normalize_number",
    "parse_date",
    "parse_number",
]
