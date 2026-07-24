"""Tests for ``python -m src.generator``."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_module_cli_writes_requested_export(tmp_path: Path) -> None:
    output = tmp_path / "patient.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.generator",
            "--seed",
            "7",
            "--years",
            "1",
            "--light",
            "--out",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["result"]["msg"] == "OK"
    assert payload["data"]["PATIENT_INFO"]["pat_id"] == "0004512-К"
    assert f"OK: {output}" in completed.stdout
    assert "приёмов:" in completed.stdout
    assert "лаб. заказов:" in completed.stdout


def test_module_cli_rejects_invalid_years(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.generator",
            "--years",
            "0",
            "--out",
            str(tmp_path / "patient.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "years must be between 1 and 30" in completed.stderr
