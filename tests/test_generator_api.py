"""Tests for the public synthetic generator API."""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from src.generator import (
    GenerationConfig,
    GenerationStats,
    generate_export,
    generate_json_bytes,
    write_export,
)


def test_generation_config_has_stable_defaults() -> None:
    assert GenerationConfig() == GenerationConfig(
        seed=42,
        years=9,
        light=False,
    )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("seed", True, TypeError),
        ("seed", "42", TypeError),
        ("years", True, TypeError),
        ("years", 0, ValueError),
        ("years", 31, ValueError),
        ("light", 1, TypeError),
    ],
)
def test_generation_config_rejects_invalid_values(
    field: str,
    value: object,
    error: type[Exception],
) -> None:
    arguments = {"seed": 42, "years": 9, "light": False}
    arguments[field] = value

    with pytest.raises(error):
        GenerationConfig(**arguments)  # type: ignore[arg-type]


def test_generate_export_does_not_mutate_global_random_state() -> None:
    random.seed(12345)
    expected = random.random()
    random.seed(12345)

    generate_export(GenerationConfig(seed=3, years=1, light=True))

    assert random.random() == expected


def test_json_bytes_are_utf8_serialization_of_payload() -> None:
    config = GenerationConfig(seed=7, years=1, light=True)

    payload = generate_export(config)
    serialized = generate_json_bytes(config)

    assert json.loads(serialized.decode("utf-8")) == payload
    assert payload["result"]["code"] == 0
    assert payload["data"]["PATIENT_INFO"]["pat_id"] == "0004512-К"


def test_write_export_creates_parent_and_returns_stats(
    tmp_path: Path,
) -> None:
    config = GenerationConfig(seed=11, years=1, light=True)
    target = tmp_path / "nested" / "patient.json"

    stats = write_export(target, config)

    content = target.read_bytes()
    payload = json.loads(content)
    assert isinstance(stats, GenerationStats)
    assert stats.line_count == len(content.splitlines())
    assert stats.size_bytes == len(content)
    assert stats.visit_count == len(payload["data"]["PRIEMY_VRACHA"])
    assert stats.laboratory_order_count == len(
        payload["data"]["lab_issledovaniya"]
    )
