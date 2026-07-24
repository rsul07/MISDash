"""Typed, serializable results for generator-to-parser quality checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from src.generator import GenerationConfig


Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True, slots=True)
class QualityCheck:
    """One named invariant with compact, reviewable evidence."""

    name: str
    passed: bool
    description: str
    evidence: tuple[str, ...]
    severity: Severity = "error"
    expected: Any = None
    actual: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "severity": self.severity,
            "description": self.description,
            "expected": self.expected,
            "actual": self.actual,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class CaseQualityReport:
    """Quality report for one generated export and parsed patient record."""

    config: GenerationConfig
    checks: tuple[QualityCheck, ...]
    duration_seconds: float

    @property
    def passed(self) -> bool:
        return all(
            check.passed or check.severity != "error"
            for check in self.checks
        )

    @property
    def failed_checks(self) -> tuple[QualityCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if not check.passed and check.severity == "error"
        )

    def check(self, name: str) -> QualityCheck:
        """Return a check by its stable name."""

        for check in self.checks:
            if check.name == name:
                return check
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "seed": self.config.seed,
                "years": self.config.years,
                "light": self.config.light,
            },
            "passed": self.passed,
            "duration_seconds": round(self.duration_seconds, 6),
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True, slots=True)
class BatchQualityReport:
    """Aggregate result for a reproducible matrix of generation configs."""

    cases: tuple[CaseQualityReport, ...]

    @property
    def passed(self) -> bool:
        return all(case.passed for case in self.cases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "case_count": len(self.cases),
            "failed_case_count": sum(
                not case.passed for case in self.cases
            ),
            "cases": [case.to_dict() for case in self.cases],
        }
