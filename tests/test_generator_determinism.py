"""Determinism tests for seeded generation and Unix timestamps."""

from __future__ import annotations

import os
import subprocess
import sys
from hashlib import sha256

from src.generator import GenerationConfig, generate_json_bytes


def test_same_seed_produces_identical_bytes() -> None:
    config = GenerationConfig(seed=17, years=1, light=True)

    first = generate_json_bytes(config)
    second = generate_json_bytes(config)

    assert first == second


def test_different_seed_changes_export() -> None:
    first = generate_json_bytes(
        GenerationConfig(seed=17, years=1, light=True)
    )
    second = generate_json_bytes(
        GenerationConfig(seed=18, years=1, light=True)
    )

    assert sha256(first).digest() != sha256(second).digest()


def test_generation_is_independent_of_process_timezone() -> None:
    assert _digest_in_timezone("UTC") == _digest_in_timezone(
        "Europe/Moscow"
    )


def _digest_in_timezone(timezone_name: str) -> str:
    code = (
        "from hashlib import sha256;"
        "from src.generator import GenerationConfig, generate_json_bytes;"
        "data=generate_json_bytes("
        "GenerationConfig(seed=7, years=1, light=True));"
        "print(sha256(data).hexdigest())"
    )
    environment = os.environ.copy()
    environment["TZ"] = timezone_name
    return subprocess.check_output(
        [sys.executable, "-c", code],
        cwd=os.getcwd(),
        env=environment,
        text=True,
    ).strip()
