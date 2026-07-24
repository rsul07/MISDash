"""Command-line entry point for reproducible pipeline quality checks."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from src.generator import GenerationConfig

from .runner import render_json, render_markdown, run_batch


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate synthetic MIS exports and verify parser invariants."
        )
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[7],
        help="one or more deterministic generator seeds",
    )
    parser.add_argument("--years", type=int, default=1)
    parser.add_argument(
        "--light",
        action="store_true",
        help="reduce visits and investigations generated per year",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
    )
    parser.add_argument(
        "--out",
        help="optional report path; stdout is used when omitted",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)
    try:
        configs = [
            GenerationConfig(
                seed=seed,
                years=arguments.years,
                light=arguments.light,
            )
            for seed in arguments.seeds
        ]
    except (TypeError, ValueError) as error:
        parser.error(str(error))

    report = run_batch(configs)
    rendered = (
        render_json(report)
        if arguments.format == "json"
        else render_markdown(report)
    )
    if arguments.out:
        target = Path(arguments.out).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        print(f"Quality report: {target}")
    else:
        print(rendered, end="")
    return 0 if report.passed else 1

