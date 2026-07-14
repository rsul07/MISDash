"""Serialization helpers for parser output contracts."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def write_profile(path: Path, profile: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as target:
        json.dump(profile, target, ensure_ascii=False, indent=2)
        target.write("\n")


def write_csv(
    path: Path,
    fields: tuple[str, ...],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: "" if row.get(field) is None else row.get(field)
                    for field in fields
                }
            )
