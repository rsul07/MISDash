"""Batch execution and human/machine-readable quality reports."""

from __future__ import annotations

import json
from collections.abc import Iterable

from src.generator import GenerationConfig

from .audit import assess_generated_case
from .models import BatchQualityReport, CaseQualityReport


def run_batch(
    configs: Iterable[GenerationConfig],
) -> BatchQualityReport:
    """Run a deterministic matrix without a hard performance threshold."""

    return BatchQualityReport(
        cases=tuple(assess_generated_case(config) for config in configs)
    )


def render_json(report: BatchQualityReport) -> str:
    return json.dumps(
        report.to_dict(),
        ensure_ascii=False,
        indent=2,
    )


def render_markdown(report: BatchQualityReport) -> str:
    status = "PASS" if report.passed else "FAIL"
    lines = [
        "# Generator → parser quality report",
        "",
        f"Overall result: **{status}**",
        "",
        (
            "Runtime is reported for observation only; "
            "there is no machine-specific performance threshold."
        ),
    ]
    for case in report.cases:
        lines.extend(_render_case(case))
    return "\n".join(lines) + "\n"


def _render_case(case: CaseQualityReport) -> list[str]:
    mode = "light" if case.config.light else "full"
    status = "PASS" if case.passed else "FAIL"
    lines = [
        "",
        (
            f"## seed={case.config.seed}, years={case.config.years}, "
            f"mode={mode}"
        ),
        "",
        f"Result: **{status}**  ",
        f"Runtime: `{case.duration_seconds:.3f} s`",
        "",
        "| Invariant | Status | Evidence |",
        "|---|---:|---|",
    ]
    for check in case.checks:
        check_status = "PASS" if check.passed else "FAIL"
        evidence = "; ".join(check.evidence) or "—"
        lines.append(
            f"| `{_escape(check.name)}` | {check_status} | "
            f"{_escape(evidence)} |"
        )
    return lines


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")

