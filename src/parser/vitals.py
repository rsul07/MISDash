"""Construction and daily aggregation of the vitals contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .constants import VITAL_BOUNDS, VITALS_FIELDS
from .extractors import extract_vitals_from_text
from .normalizers import clean_text, normalize_date, valid_bp_pair, valid_number
from .records import as_mapping, first, records, truthy_flag, unique_visits


def build_vitals(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _VitalsBuilder(data).build()


class _VitalsBuilder:
    def __init__(self, data: Mapping[str, Any]) -> None:
        self.data = data

    def build(self) -> list[dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}

        # Apply sources from lower to higher clinical priority. Values within
        # one source and calendar day are averaged deterministically.
        self._add_diary_vitals(rows)
        self._add_direct_vitals(rows)
        self._add_laboratory_vitals(rows)
        self._add_visit_vitals(rows)

        return [
            rows[measurement_date]
            for measurement_date in sorted(rows)
            if any(
                rows[measurement_date].get(field) is not None
                for field in VITALS_FIELDS
                if field != "date"
            )
        ]

    def _add_diary_vitals(self, rows: dict[str, dict[str, Any]]) -> None:
        diary = first(
            self.data,
            "dnevnik_samokontrolya",
            "self_monitoring_diary",
            "self_monitoring",
        )
        diary_mapping = as_mapping(diary)
        bp_source = first(
            diary_mapping,
            "AD_izmereniya",
            "ad_izmereniya",
            "blood_pressure",
            "bp",
        )
        glucose_source = first(
            diary_mapping,
            "glikemiya",
            "glycemia",
            "glucose",
        )

        samples: dict[tuple[str, str], list[float]] = {}
        for measurement in records(bp_source):
            measurement_date = normalize_date(
                first(measurement, "dt", "date", "measured_at", "izmereno")
            )
            bp_pair = valid_bp_pair(
                first(measurement, "sys", "sys_bp", "systolic"),
                first(measurement, "dia", "dia_bp", "diastolic"),
            )
            if bp_pair is not None:
                self._collect_sample(samples, measurement_date, "sys_bp", bp_pair[0])
                self._collect_sample(samples, measurement_date, "dia_bp", bp_pair[1])
            self._collect_sample(
                samples,
                measurement_date,
                "heart_rate",
                first(measurement, "pulse", "heart_rate", "CHSS"),
                20,
                250,
            )

        for measurement in records(glucose_source):
            measurement_date = normalize_date(
                first(measurement, "izmereno", "dt", "date", "measured_at")
            )
            self._collect_sample(
                samples,
                measurement_date,
                "glucose",
                first(measurement, "glukoza_mmol", "glucose", "value", "REZULT"),
                *VITAL_BOUNDS["glucose"],
            )
        self._apply_daily_samples(
            rows, samples, integer_fields={"sys_bp", "dia_bp", "heart_rate"}
        )

    def _add_direct_vitals(self, rows: dict[str, dict[str, Any]]) -> None:
        source = first(self.data, "vitals", "vital_signs", "measurements")
        aliases = {
            "heart_rate": ("heart_rate", "pulse", "CHSS"),
            "weight": ("weight", "weight_kg", "ves"),
            "glucose": ("glucose", "glukoza_mmol"),
            "hba1c": ("hba1c", "HbA1c"),
            "creatinine": ("creatinine", "kreatinin"),
            "cholesterol": ("cholesterol", "total_cholesterol"),
        }
        samples: dict[tuple[str, str], list[float]] = {}
        for measurement in records(source):
            measurement_date = normalize_date(
                first(measurement, "date", "dt", "measured_at", "izmereno")
            )
            bp_pair = valid_bp_pair(
                first(measurement, "sys_bp", "sys", "systolic", "AD_sist"),
                first(measurement, "dia_bp", "dia", "diastolic", "AD_diast"),
            )
            if bp_pair is not None:
                self._collect_sample(samples, measurement_date, "sys_bp", bp_pair[0])
                self._collect_sample(samples, measurement_date, "dia_bp", bp_pair[1])
            for field, field_aliases in aliases.items():
                self._collect_sample(
                    samples,
                    measurement_date,
                    field,
                    first(measurement, *field_aliases),
                    *VITAL_BOUNDS[field],
                )
        self._apply_daily_samples(
            rows, samples, integer_fields={"sys_bp", "dia_bp", "heart_rate"}
        )

    def _add_laboratory_vitals(self, rows: dict[str, dict[str, Any]]) -> None:
        source = first(
            self.data,
            "lab_issledovaniya",
            "laboratory_tests",
            "laboratory",
            "labs",
        )
        samples: dict[tuple[str, str], list[float]] = {}
        for panel in records(source):
            panel_date = normalize_date(
                first(
                    panel,
                    "data_vzyatia",
                    "date",
                    "collected_at",
                    "data_gotovnosti",
                )
            )
            results_source = first(
                panel, "REZULTATY", "rezultaty", "results", "indicators"
            )
            result_records = records(results_source)
            if not result_records and first(
                panel, "pokazatel", "indicator", "test_name"
            ) is not None:
                result_records = [panel]

            for result in result_records:
                if truthy_flag(first(result, "is_deleted", "deleted")):
                    continue
                indicator = clean_text(
                    first(result, "pokazatel", "indicator", "test_name", "name")
                )
                field = _lab_field(indicator)
                if field is None:
                    continue
                result_date = normalize_date(
                    first(result, "date", "dt_validacii", "validated_at")
                )
                self._collect_sample(
                    samples,
                    panel_date or result_date,
                    field,
                    first(
                        result,
                        "REZULT",
                        "REZULTAT",
                        "result",
                        "value",
                        "znachenie",
                    ),
                    *VITAL_BOUNDS[field],
                )
        self._apply_daily_samples(rows, samples)

    def _add_visit_vitals(self, rows: dict[str, dict[str, Any]]) -> None:
        source = first(
            self.data,
            "PRIEMY_VRACHA",
            "priemy_vracha",
            "visits",
            "appointments",
        )
        samples: dict[tuple[str, str], list[float]] = {}
        for visit in unique_visits(source):
            visit_date = normalize_date(
                first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
            )
            if visit_date is None:
                continue

            measurements = as_mapping(
                first(visit, "izmereniya", "measurements", "vitals")
            )
            objective = extract_vitals_from_text(
                first(
                    visit,
                    "obektivny_status",
                    "objective_status",
                    "objective",
                    "OBJECTIVE",
                )
            )
            complaints = extract_vitals_from_text(
                first(visit, "JALOBY_TXT", "jaloby_txt", "complaints", "jaloby")
            )

            structured_bp = valid_bp_pair(
                first(measurements, "AD_sist", "sys_bp", "sys", "systolic"),
                first(measurements, "AD_diast", "dia_bp", "dia", "diastolic"),
            )
            objective_bp = valid_bp_pair(objective["sys_bp"], objective["dia_bp"])
            complaints_bp = valid_bp_pair(complaints["sys_bp"], complaints["dia_bp"])
            blood_pressure = structured_bp or objective_bp or complaints_bp

            heart_rate = valid_number(
                first(measurements, "CHSS", "heart_rate", "pulse"), 20, 250
            )
            if heart_rate is None:
                heart_rate = valid_number(objective["heart_rate"], 20, 250)
            if heart_rate is None:
                heart_rate = valid_number(complaints["heart_rate"], 20, 250)
            weight = valid_number(
                first(measurements, "ves", "weight", "weight_kg"), 1, 500
            )

            if blood_pressure is not None:
                self._collect_sample(samples, visit_date, "sys_bp", blood_pressure[0])
                self._collect_sample(samples, visit_date, "dia_bp", blood_pressure[1])
            self._collect_sample(samples, visit_date, "heart_rate", heart_rate)
            self._collect_sample(samples, visit_date, "weight", weight)
        self._apply_daily_samples(
            rows, samples, integer_fields={"sys_bp", "dia_bp", "heart_rate"}
        )

    @staticmethod
    def _collect_sample(
        samples: dict[tuple[str, str], list[float]],
        measurement_date: str | None,
        field: str,
        value: Any,
        minimum: float | None = None,
        maximum: float | None = None,
    ) -> None:
        if measurement_date is None:
            return
        number = valid_number(value, minimum, maximum)
        if number is not None:
            samples.setdefault((measurement_date, field), []).append(number)

    @classmethod
    def _apply_daily_samples(
        cls,
        rows: dict[str, dict[str, Any]],
        samples: Mapping[tuple[str, str], list[float]],
        integer_fields: set[str] | None = None,
    ) -> None:
        integer_fields = integer_fields or set()
        for (measurement_date, field), values in samples.items():
            if not values:
                continue
            average = sum(values) / len(values)
            value: int | float
            if field in integer_fields:
                value = int(round(average))
            else:
                value = round(average, 2)
            row = cls._vitals_row(rows, measurement_date)
            if row is not None:
                row[field] = value

    @staticmethod
    def _vitals_row(
        rows: dict[str, dict[str, Any]], measurement_date: str | None
    ) -> dict[str, Any] | None:
        if measurement_date is None:
            return None
        if measurement_date not in rows:
            rows[measurement_date] = {
                field: measurement_date if field == "date" else None
                for field in VITALS_FIELDS
            }
        return rows[measurement_date]


def _lab_field(indicator: str) -> str | None:
    normalized = indicator.casefold().replace("ё", "е").strip()
    if (
        normalized in {"глюкоза", "glucose"}
        or "глюкоз" in normalized
        and "моч" not in normalized
    ):
        return "glucose"
    if "hba1c" in normalized or "гликирован" in normalized:
        return "hba1c"
    if (
        normalized in {"креатинин", "creatinine"}
        or "креатинин" in normalized
        and "моч" not in normalized
    ):
        return "creatinine"
    if normalized in {
        "холестерин общий",
        "общий холестерин",
        "total cholesterol",
        "cholesterol",
    }:
        return "cholesterol"
    return None
