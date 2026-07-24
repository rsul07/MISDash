"""Regression parity with the tracked full synthetic reference export."""

from hashlib import sha256
from pathlib import Path

from src.generator import GenerationConfig, generate_json_bytes


REFERENCE_SHA256 = (
    "7eb74375be9c5f76d595792639dbaaeb4ddbb6faa08c6760c272da049f3980b8"
)


def test_default_generation_matches_patient_etalon() -> None:
    expected = (
        Path(__file__).parents[1] / "data" / "patient_etalon.json"
    ).read_bytes()

    actual = generate_json_bytes(
        GenerationConfig(seed=42, years=9, light=False)
    )

    assert sha256(actual).hexdigest() == REFERENCE_SHA256
    assert actual == expected
