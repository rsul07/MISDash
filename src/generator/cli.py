"""Command-line interface for the synthetic MIS generator."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .models import GenerationConfig
from .service import write_export


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a deliberately dirty synthetic MIS JSON export."
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--years",
        type=int,
        default=9,
        help="глубина истории наблюдения",
    )
    parser.add_argument(
        "--light",
        action="store_true",
        help="уменьшенный объём приёмов и исследований",
    )
    parser.add_argument("--out", default="patient_demo.json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)
    try:
        config = GenerationConfig(
            seed=arguments.seed,
            years=arguments.years,
            light=arguments.light,
        )
    except (TypeError, ValueError) as error:
        parser.error(str(error))

    stats = write_export(arguments.out, config)
    print(
        f"OK: {arguments.out} — {stats.line_count} строк, "
        f"{stats.size_bytes / 1e6:.1f} МБ, "
        f"приёмов: {stats.visit_count}, "
        f"лаб. заказов: {stats.laboratory_order_count}"
    )
    return 0
