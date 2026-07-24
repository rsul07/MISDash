"""Public generation, serialization, and filesystem services."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from .builder import build_export
from .models import GenerationConfig, GenerationStats


DEFAULT_CONFIG = GenerationConfig()


def generate_export(
    config: GenerationConfig = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Generate one deterministic in-memory dirty MIS export."""

    return build_export(random.Random(config.seed), config)


def generate_json_bytes(
    config: GenerationConfig = DEFAULT_CONFIG,
) -> bytes:
    """Generate the export using its canonical UTF-8 JSON representation."""

    return _serialize(generate_export(config))


def write_export(
    path: str | Path,
    config: GenerationConfig = DEFAULT_CONFIG,
) -> GenerationStats:
    """Generate and write an export, returning compact artifact statistics."""

    payload = generate_export(config)
    content = _serialize(payload)
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return _stats(payload, content)


def _serialize(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")


def _stats(
    payload: dict[str, Any],
    content: bytes,
) -> GenerationStats:
    data = payload["data"]
    return GenerationStats(
        line_count=len(content.splitlines()),
        size_bytes=len(content),
        visit_count=len(data["PRIEMY_VRACHA"]),
        laboratory_order_count=len(data["lab_issledovaniya"]),
    )
