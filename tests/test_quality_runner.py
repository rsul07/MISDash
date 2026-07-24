"""Tests for batch rendering and the ``src.quality`` CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.generator import GenerationConfig
from src.quality import render_json, render_markdown, run_batch


def test_batch_report_has_machine_and_reviewer_formats() -> None:
    report = run_batch(
        [GenerationConfig(seed=7, years=1, light=True)]
    )

    json_payload = json.loads(render_json(report))
    markdown = render_markdown(report)

    assert report.passed
    assert json_payload["passed"] is True
    assert json_payload["case_count"] == 1
    assert "Runtime is reported for observation only" in markdown
    assert "`provenance.paths_resolve`" in markdown


def test_module_cli_writes_json_report(tmp_path: Path) -> None:
    output = tmp_path / "quality.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.quality",
            "--seeds",
            "7",
            "--years",
            "1",
            "--light",
            "--format",
            "json",
            "--out",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["cases"][0]["config"] == {
        "seed": 7,
        "years": 1,
        "light": True,
    }
    assert f"Quality report: {output}" in completed.stdout
