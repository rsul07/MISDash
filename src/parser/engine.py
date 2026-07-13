"""Fault-tolerant parser for dirty MIS patient exports."""

from __future__ import annotations

import csv
import json
import math
import os
import re
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = "data/processed/"

PROFILE_FIELDS = (
    "fio",
    "birth_date",
    "age",
    "gender",
    "blood_group",
    "bmi",
    "allergies",
    "chronic_diseases",
    "current_therapy",
)
VITALS_FIELDS = (
    "date",
    "sys_bp",
    "dia_bp",
    "heart_rate",
    "weight",
    "glucose",
    "hba1c",
    "creatinine",
    "cholesterol",
)
VISITS_FIELDS = ("date", "doctor", "specialty", "diagnosis", "complaints")

_VITAL_BOUNDS: dict[str, tuple[float | None, float | None]] = {
    "sys_bp": (60, 300),
    "dia_bp": (30, 200),
    "heart_rate": (20, 250),
    "weight": (1, 500),
    "glucose": (0, 100),
    "hba1c": (0, 30),
    "creatinine": (0, 10_000),
    "cholesterol": (0, 100),
}

_MISSING_STRINGS = {
    "",
    "-",
    "н/д",
    "нет данных",
    "null",
    "none",
    "nan",
}
_RECORD_HINT_KEYS = {
    "id_priema",
    "visit_id",
    "dt_priem",
    "date",
    "vrach",
    "doctor",
    "diagnoz_priema",
    "diagnosis",
    "izmereniya",
    "measurements",
    "data_vzyatia",
    "rezultaty",
    "results",
    "pokazatel",
    "indicator",
    "dt",
    "izmereno",
    "sys",
    "dia",
    "pulse",
    "agent",
    "agent_name",
    "diagnoz_name",
    "preparat",
}

_BP_RE = re.compile(
    r"(?:\b[АA]Д\b|\bА\s*/\s*Д\b|\bAD\b|"
    r"артериальн\w*\s+давлен\w*|\bдавлен\w*)"
    r"[^0-9]{0,50}"
    r"(?P<sys>\d{2,3})\s*(?:[/\\-]|\bна\b)\s*(?P<dia>\d{2,3})\b",
    flags=re.IGNORECASE,
)
_HEART_RATE_RE = re.compile(
    r"\b(?:ЧСС|пульс(?:а)?|HR)\b[^0-9]{0,20}(?P<heart_rate>\d{2,3})\b",
    flags=re.IGNORECASE,
)


def normalize_date(value: Any) -> str | None:
    """Convert a supported dirty date value to ``YYYY-MM-DD``.

    Besides the formats required by the data contract, this function accepts
    the additional compact and date-time formats emitted by the current data
    generator. Unix timestamps are interpreted in UTC so results do not depend
    on the machine's local timezone.
    """

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        if float(value).is_integer() and 1000 <= int(value) <= 9999:
            return None
        if float(value).is_integer() and re.fullmatch(r"\d{8}", str(int(value))):
            try:
                return datetime.strptime(str(int(value)), "%Y%m%d").date().isoformat()
            except ValueError:
                pass
        return _date_from_timestamp(value)
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if raw.casefold() in _MISSING_STRINGS:
        return None

    # Check compact calendar dates before numeric timestamps.
    if re.fullmatch(r"\d{8}", raw):
        try:
            return datetime.strptime(raw, "%Y%m%d").date().isoformat()
        except ValueError:
            pass

    if re.fullmatch(r"\d{4}", raw) and 1000 <= int(raw) <= 9999:
        return None

    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", raw):
        try:
            return _date_from_timestamp(float(raw))
        except ValueError:
            return None

    iso_candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        return datetime.fromisoformat(iso_candidate).date().isoformat()
    except ValueError:
        pass

    formats = (
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d.%m.%y",
        "%d/%m/%y",
        "%d.%m.%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%d.%m.%y %H:%M",
        "%d/%m/%y %H:%M",
    )
    for date_format in formats:
        try:
            return datetime.strptime(raw, date_format).date().isoformat()
        except ValueError:
            continue
    return None


def _date_from_timestamp(value: int | float) -> str | None:
    if not math.isfinite(float(value)):
        return None

    timestamp = float(value)
    # Accept seconds as well as common millisecond/microsecond encodings.
    while abs(timestamp) > 10_000_000_000:
        timestamp /= 1000
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def parse_number(value: Any) -> float | None:
    """Convert a number or a decimal string (including comma decimals)."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if not isinstance(value, str):
        return None

    raw = value.strip().replace("\u00a0", "")
    if raw.casefold() in _MISSING_STRINGS:
        return None
    raw = raw.replace(" ", "").replace(",", ".")
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", raw):
        return None
    try:
        number = float(raw)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


# Friendly aliases for callers that use either parsing or normalization terms.
parse_date = normalize_date
normalize_number = parse_number


def extract_vitals_from_text(value: Any) -> dict[str, int | None]:
    """Extract blood pressure and heart rate from free-form Russian text."""

    text = _clean_text(value)
    result: dict[str, int | None] = {
        "sys_bp": None,
        "dia_bp": None,
        "heart_rate": None,
    }
    if not text:
        return result

    for bp_match in _BP_RE.finditer(text):
        systolic = int(bp_match.group("sys"))
        diastolic = int(bp_match.group("dia"))
        if _valid_bp_pair(systolic, diastolic) is not None:
            result["sys_bp"] = systolic
            result["dia_bp"] = diastolic
            break

    for heart_rate_match in _HEART_RATE_RE.finditer(text):
        heart_rate = int(heart_rate_match.group("heart_rate"))
        if 20 <= heart_rate <= 250:
            result["heart_rate"] = heart_rate
            break
    return result


class MISParser:
    """Parse one MIS JSON export and save dashboard-ready data files."""

    profile_fields = PROFILE_FIELDS
    vitals_fields = VITALS_FIELDS
    visits_fields = VISITS_FIELDS
    normalize_date = staticmethod(normalize_date)
    parse_date = staticmethod(normalize_date)
    parse_number = staticmethod(parse_number)
    normalize_number = staticmethod(parse_number)
    extract_vitals_from_text = staticmethod(extract_vitals_from_text)

    def __init__(
        self,
        input_path: str | os.PathLike[str],
        output_dir: str | os.PathLike[str] | None = None,
    ) -> None:
        self.input_path = Path(input_path).expanduser()
        configured_output = (
            output_dir
            if output_dir is not None
            else os.getenv("OUTPUT_DIR") or DEFAULT_OUTPUT_DIR
        )
        self.output_dir = Path(configured_output).expanduser()

    def parse(self) -> dict[str, Path]:
        """Parse the input and return paths of the three generated files."""

        payload = self._load_json()
        data = self._medical_data(payload)
        profile = self._build_profile(data)
        visits = self._build_visits(data)
        vitals = self._build_vitals(data)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "profile": self.output_dir / "profile.json",
            "vitals": self.output_dir / "vitals.csv",
            "visits": self.output_dir / "visits.csv",
        }
        self._write_profile(paths["profile"], profile)
        self._write_csv(paths["vitals"], VITALS_FIELDS, vitals)
        self._write_csv(paths["visits"], VISITS_FIELDS, visits)
        return paths

    def run(self) -> dict[str, Path]:
        """Alias for :meth:`parse` for command-style callers."""

        return self.parse()

    def _load_json(self) -> Any:
        try:
            with self.input_path.open(encoding="utf-8-sig") as source:
                return json.load(source)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON in {self.input_path}: {error.msg}") from error

    @staticmethod
    def _medical_data(payload: Any) -> Mapping[str, Any]:
        root = _as_mapping(payload)
        nested = _first(root, "data")
        return _as_mapping(nested) if isinstance(nested, Mapping) else root

    def _build_profile(self, data: Mapping[str, Any]) -> dict[str, Any]:
        patient = _as_mapping(
            _first(data, "PATIENT_INFO", "patient_info", "patient", "profile")
        )
        visits = _unique_visits(
            _first(data, "PRIEMY_VRACHA", "priemy_vracha", "visits", "appointments")
        )

        fio = _clean_name(_first(patient, "FIO", "fio", "full_name", "name"))
        if not fio:
            fio = _clean_name(
                " ".join(
                    part
                    for part in (
                        _clean_text(_first(patient, "pat_fam", "last_name")),
                        _clean_text(_first(patient, "pat_im", "first_name")),
                        _clean_text(_first(patient, "pat_otch", "middle_name")),
                    )
                    if part
                )
            )

        birth_date = normalize_date(
            _first(
                patient,
                "birht_date",
                "birtf_date",
                "birth_date",
                "DATE_ROJD",
                "date_rojd",
            )
        )
        age = _age_from_values(_first(patient, "age", "vozrast"), birth_date)
        gender = _normalize_gender(
            _first(patient, "gender", "sex", "pol", "SEX_ID", "sex_id")
        )
        blood_group = _clean_text(
            _first(patient, "blood_grp", "blood_group", "gruppa_krovi")
        )

        bmi = parse_number(_first(patient, "bmi", "BMI", "IMT", "imt"))
        if bmi is None:
            height = parse_number(_first(patient, "rost_sm", "height", "height_cm", "rost"))
            weight = parse_number(
                _first(patient, "ves_kg_last", "weight", "weight_kg", "ves")
            )
            if weight is None:
                weight = self._latest_visit_measurement(visits, "ves", "weight", "weight_kg")
            if height is None:
                height = self._latest_visit_measurement(visits, "rost", "height", "height_cm")
            if weight is not None and height is not None and height > 0:
                bmi = weight / ((height / 100) ** 2)
        if bmi is not None:
            bmi = round(bmi, 1)

        social = _as_mapping(
            _first(data, "social_anamnez", "social_history", "social_anamnesis")
        )
        allergies_source = _first(
            social,
            "allergoanamnez",
            "allergies",
            "allergy_history",
        )
        if allergies_source is None:
            allergies_source = _first(patient, "allergies", "allergoanamnez")

        chronic_source = _first(
            data,
            "hron_zabolevaniya",
            "chronic_diseases",
            "chronic_conditions",
        )
        direct_therapy = _first(patient, "current_therapy", "terapiya", "therapy")
        current_therapy = self._format_therapy(direct_therapy)
        if not current_therapy:
            current_therapy = self._latest_therapy(visits)

        return {
            "fio": fio,
            "birth_date": birth_date or "",
            "age": age,
            "gender": gender,
            "blood_group": blood_group,
            "bmi": bmi,
            "allergies": self._extract_allergies(allergies_source),
            "chronic_diseases": self._extract_chronic_diseases(chronic_source),
            "current_therapy": current_therapy,
        }

    @staticmethod
    def _extract_allergies(source: Any) -> list[str]:
        allergies: list[str] = []
        for record in _items(source):
            if isinstance(record, Mapping):
                note = _clean_text(
                    _first(record, "note", "prim", "comment", "description")
                )
                if "дубл" in note.casefold() or _truthy_flag(
                    _first(record, "is_deleted", "deleted")
                ):
                    continue
                agent = _clean_text(
                    _first(record, "agent", "AGENT_NAME", "allergen", "name")
                )
                reaction = _clean_text(
                    _first(record, "reakciya", "react", "reaction", "response")
                )
                value = f"{agent} ({reaction})" if agent and reaction else agent or reaction
            elif isinstance(record, str):
                value = _clean_text(record)
            else:
                value = ""
            if value:
                allergies.append(value)
        return _deduplicate(allergies)

    @staticmethod
    def _extract_chronic_diseases(source: Any) -> list[str]:
        diseases: list[str] = []
        for record in _items(source):
            if isinstance(record, Mapping):
                value = _clean_text(
                    _first(
                        record,
                        "DIAGNOZ_NAME",
                        "diagnoz_name",
                        "diagnosis",
                        "name",
                        "MKB10_KOD",
                        "code",
                    )
                )
            elif isinstance(record, str):
                value = _clean_text(record)
            else:
                value = ""
            if value:
                diseases.append(value)
        return _deduplicate(diseases)

    @staticmethod
    def _format_therapy(source: Any) -> list[str]:
        therapy: list[str] = []
        for record in _items(source):
            if isinstance(record, Mapping):
                parts = (
                    _clean_text(
                        _first(record, "preparat", "drug", "medication", "name")
                    ),
                    _clean_text(_first(record, "doza", "dose")),
                    _clean_text(_first(record, "krat", "frequency", "schedule")),
                )
                value = " ".join(part for part in parts if part)
            elif isinstance(record, str):
                value = _clean_text(record)
            else:
                value = ""
            if value:
                therapy.append(value)
        return _deduplicate(therapy)

    def _latest_therapy(self, visits: list[Mapping[str, Any]]) -> list[str]:
        latest_key: tuple[bool, str, int] | None = None
        latest_therapy: list[str] = []
        for index, visit in enumerate(visits):
            therapy = self._format_therapy(
                _first(visit, "terapiya", "therapy", "medications", "current_therapy")
            )
            if not therapy:
                continue
            visit_date = normalize_date(
                _first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
            )
            candidate_key = (visit_date is not None, visit_date or "", index)
            if latest_key is None or candidate_key > latest_key:
                latest_key = candidate_key
                latest_therapy = therapy
        return latest_therapy

    @staticmethod
    def _latest_visit_measurement(
        visits: list[Mapping[str, Any]], *keys: str
    ) -> float | None:
        candidates: list[tuple[tuple[bool, str, int], float]] = []
        for index, visit in enumerate(visits):
            measurements = _as_mapping(
                _first(visit, "izmereniya", "measurements", "vitals")
            )
            value = parse_number(_first(measurements, *keys))
            if value is None:
                continue
            visit_date = normalize_date(
                _first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
            )
            candidates.append(((visit_date is not None, visit_date or "", index), value))
        if not candidates:
            return None
        return max(candidates, key=lambda candidate: candidate[0])[1]

    def _build_visits(self, data: Mapping[str, Any]) -> list[dict[str, Any]]:
        source = _first(
            data,
            "PRIEMY_VRACHA",
            "priemy_vracha",
            "visits",
            "appointments",
        )
        rows: list[dict[str, Any]] = []
        for visit in _unique_visits(source):
            doctor_data = _first(visit, "VRACH", "vrach", "doctor", "physician")
            doctor_mapping = _as_mapping(doctor_data)
            doctor = _clean_text(
                _first(doctor_mapping, "fio_doc", "FIO", "fio", "name", "doctor")
            )
            if not doctor:
                doctor = _clean_text(doctor_data)
            specialty = _clean_text(
                _first(
                    doctor_mapping,
                    "spec_name",
                    "specialty",
                    "speciality",
                    "specialization",
                )
            ) or _clean_text(_first(visit, "specialty", "spec_name"))

            diagnosis_data = _first(
                visit, "diagnoz_priema", "diagnosis", "diagnoz", "visit_diagnosis"
            )
            diagnosis_mapping = _as_mapping(diagnosis_data)
            diagnosis = _clean_text(
                _first(
                    diagnosis_mapping,
                    "osnovnoy_txt",
                    "diagnosis",
                    "diagnoz",
                    "name",
                    "osnovnoy_MKB",
                    "code",
                )
            )
            if not diagnosis:
                diagnosis = _clean_text(diagnosis_data)

            row = {
                "date": normalize_date(
                    _first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
                )
                or "",
                "doctor": doctor,
                "specialty": specialty,
                "diagnosis": diagnosis,
                "complaints": _clean_text(
                    _first(visit, "JALOBY_TXT", "jaloby_txt", "complaints", "jaloby")
                ),
            }
            if not any(row.values()):
                continue
            rows.append(row)
        rows.sort(key=lambda row: (not bool(row["date"]), row["date"]))
        return rows

    def _build_vitals(self, data: Mapping[str, Any]) -> list[dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}

        # Sources are applied from lower to higher clinical priority. Values
        # within one source and calendar day are averaged deterministically.
        self._add_diary_vitals(data, rows)
        self._add_direct_vitals(data, rows)
        self._add_laboratory_vitals(data, rows)
        self._add_visit_vitals(data, rows)

        return [
            rows[measurement_date]
            for measurement_date in sorted(rows)
            if any(
                rows[measurement_date].get(field) is not None
                for field in VITALS_FIELDS
                if field != "date"
            )
        ]

    def _add_diary_vitals(
        self, data: Mapping[str, Any], rows: dict[str, dict[str, Any]]
    ) -> None:
        diary = _first(
            data,
            "dnevnik_samokontrolya",
            "self_monitoring_diary",
            "self_monitoring",
        )
        diary_mapping = _as_mapping(diary)
        bp_source = _first(
            diary_mapping,
            "AD_izmereniya",
            "ad_izmereniya",
            "blood_pressure",
            "bp",
        )
        glucose_source = _first(
            diary_mapping,
            "glikemiya",
            "glycemia",
            "glucose",
        )

        samples: dict[tuple[str, str], list[float]] = {}
        for measurement in _records(bp_source):
            measurement_date = normalize_date(
                _first(measurement, "dt", "date", "measured_at", "izmereno")
            )
            bp_pair = _valid_bp_pair(
                _first(measurement, "sys", "sys_bp", "systolic"),
                _first(measurement, "dia", "dia_bp", "diastolic"),
            )
            if bp_pair is not None:
                self._collect_sample(
                    samples, measurement_date, "sys_bp", bp_pair[0]
                )
                self._collect_sample(
                    samples, measurement_date, "dia_bp", bp_pair[1]
                )
            self._collect_sample(
                samples,
                measurement_date,
                "heart_rate",
                _first(measurement, "pulse", "heart_rate", "CHSS"),
                20,
                250,
            )

        for measurement in _records(glucose_source):
            measurement_date = normalize_date(
                _first(measurement, "izmereno", "dt", "date", "measured_at")
            )
            self._collect_sample(
                samples,
                measurement_date,
                "glucose",
                _first(measurement, "glukoza_mmol", "glucose", "value", "REZULT"),
                *_VITAL_BOUNDS["glucose"],
            )
        self._apply_daily_samples(
            rows, samples, integer_fields={"sys_bp", "dia_bp", "heart_rate"}
        )

    def _add_direct_vitals(
        self, data: Mapping[str, Any], rows: dict[str, dict[str, Any]]
    ) -> None:
        source = _first(data, "vitals", "vital_signs", "measurements")
        aliases = {
            "heart_rate": ("heart_rate", "pulse", "CHSS"),
            "weight": ("weight", "weight_kg", "ves"),
            "glucose": ("glucose", "glukoza_mmol"),
            "hba1c": ("hba1c", "HbA1c"),
            "creatinine": ("creatinine", "kreatinin"),
            "cholesterol": ("cholesterol", "total_cholesterol"),
        }
        samples: dict[tuple[str, str], list[float]] = {}
        for measurement in _records(source):
            measurement_date = normalize_date(
                _first(measurement, "date", "dt", "measured_at", "izmereno")
            )
            bp_pair = _valid_bp_pair(
                _first(measurement, "sys_bp", "sys", "systolic", "AD_sist"),
                _first(measurement, "dia_bp", "dia", "diastolic", "AD_diast"),
            )
            if bp_pair is not None:
                self._collect_sample(
                    samples, measurement_date, "sys_bp", bp_pair[0]
                )
                self._collect_sample(
                    samples, measurement_date, "dia_bp", bp_pair[1]
                )
            for field, field_aliases in aliases.items():
                self._collect_sample(
                    samples,
                    measurement_date,
                    field,
                    _first(measurement, *field_aliases),
                    *_VITAL_BOUNDS[field],
                )
        self._apply_daily_samples(
            rows, samples, integer_fields={"sys_bp", "dia_bp", "heart_rate"}
        )

    def _add_laboratory_vitals(
        self, data: Mapping[str, Any], rows: dict[str, dict[str, Any]]
    ) -> None:
        source = _first(
            data,
            "lab_issledovaniya",
            "laboratory_tests",
            "laboratory",
            "labs",
        )
        samples: dict[tuple[str, str], list[float]] = {}
        for panel in _records(source):
            panel_date = normalize_date(
                _first(
                    panel,
                    "data_vzyatia",
                    "date",
                    "collected_at",
                    "data_gotovnosti",
                )
            )
            results_source = _first(
                panel, "REZULTATY", "rezultaty", "results", "indicators"
            )
            results = _records(results_source)
            if not results and _first(panel, "pokazatel", "indicator", "test_name") is not None:
                results = [panel]

            for result in results:
                if _truthy_flag(_first(result, "is_deleted", "deleted")):
                    continue
                indicator = _clean_text(
                    _first(result, "pokazatel", "indicator", "test_name", "name")
                )
                field = _lab_field(indicator)
                if field is None:
                    continue
                result_date = normalize_date(
                    _first(result, "date", "dt_validacii", "validated_at")
                )
                measurement_date = panel_date or result_date
                self._collect_sample(
                    samples,
                    measurement_date,
                    field,
                    _first(
                        result,
                        "REZULT",
                        "REZULTAT",
                        "result",
                        "value",
                        "znachenie",
                    ),
                    *_VITAL_BOUNDS[field],
                )
        self._apply_daily_samples(rows, samples)

    def _add_visit_vitals(
        self, data: Mapping[str, Any], rows: dict[str, dict[str, Any]]
    ) -> None:
        source = _first(
            data,
            "PRIEMY_VRACHA",
            "priemy_vracha",
            "visits",
            "appointments",
        )
        samples: dict[tuple[str, str], list[float]] = {}
        for visit in _unique_visits(source):
            visit_date = normalize_date(
                _first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
            )
            if visit_date is None:
                continue

            measurements = _as_mapping(
                _first(visit, "izmereniya", "measurements", "vitals")
            )
            objective = extract_vitals_from_text(
                _first(
                    visit,
                    "obektivny_status",
                    "objective_status",
                    "objective",
                    "OBJECTIVE",
                )
            )
            complaints = extract_vitals_from_text(
                _first(visit, "JALOBY_TXT", "jaloby_txt", "complaints", "jaloby")
            )

            structured_bp = _valid_bp_pair(
                _first(measurements, "AD_sist", "sys_bp", "sys", "systolic"),
                _first(measurements, "AD_diast", "dia_bp", "dia", "diastolic"),
            )
            objective_bp = _valid_bp_pair(
                objective["sys_bp"], objective["dia_bp"]
            )
            complaints_bp = _valid_bp_pair(
                complaints["sys_bp"], complaints["dia_bp"]
            )
            blood_pressure = structured_bp or objective_bp or complaints_bp

            heart_rate = _valid_number(
                _first(measurements, "CHSS", "heart_rate", "pulse"), 20, 250
            )
            if heart_rate is None:
                heart_rate = _valid_number(objective["heart_rate"], 20, 250)
            if heart_rate is None:
                heart_rate = _valid_number(complaints["heart_rate"], 20, 250)
            weight = _valid_number(
                _first(measurements, "ves", "weight", "weight_kg"), 1, 500
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
        number = _valid_number(value, minimum, maximum)
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

    @staticmethod
    def _write_profile(path: Path, profile: Mapping[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as target:
            json.dump(profile, target, ensure_ascii=False, indent=2)
            target.write("\n")

    @staticmethod
    def _write_csv(
        path: Path,
        fields: tuple[str, ...],
        rows: Iterable[Mapping[str, Any]],
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        field: "" if row.get(field) is None else row.get(field)
                        for field in fields
                    }
                )


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    if not isinstance(mapping, Mapping):
        return None
    for key in keys:
        value = mapping.get(key)
        if _has_value(value):
            return value

    folded = {
        key.casefold(): value
        for key, value in mapping.items()
        if isinstance(key, str)
    }
    for key in keys:
        value = folded.get(key.casefold())
        if _has_value(value):
            return value
    return None


def _records(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if not value:
            return []
        keys = {
            key.casefold()
            for key in value
            if isinstance(key, str)
        }
        if keys & _RECORD_HINT_KEYS:
            return [value]
        nested = list(value.values())
        if nested and all(isinstance(item, Mapping) for item in nested):
            return [item for item in nested if isinstance(item, Mapping)]
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _clean_text(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        cleaned = " ".join(value.replace("\u00a0", " ").split())
        return "" if cleaned.casefold() in _MISSING_STRINGS else cleaned
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return "; ".join(filter(None, (_clean_text(item) for item in value)))
    return ""


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().casefold() not in _MISSING_STRINGS
    return True


def _clean_name(value: Any) -> str:
    text = _clean_text(value)
    return text.title() if text and text == text.upper() else text


def _normalize_gender(value: Any) -> str:
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, (int, float)):
        if value == 1:
            return "Мужской"
        if value == 2:
            return "Женский"
    text = _clean_text(value)
    normalized = text.casefold()
    if normalized in {"м", "муж", "мужской", "male", "m", "1"}:
        return "Мужской"
    if normalized in {"ж", "жен", "женский", "female", "f", "2"}:
        return "Женский"
    return text


def _age_from_values(raw_age: Any, birth_date: str | None) -> int | None:
    age = parse_number(raw_age)
    if age is not None and age >= 0:
        return int(age)
    if birth_date is None:
        return None
    try:
        born = date.fromisoformat(birth_date)
    except ValueError:
        return None
    today = date.today()
    calculated = today.year - born.year - (
        (today.month, today.day) < (born.month, born.day)
    )
    return calculated if calculated >= 0 else None


def _valid_number(
    value: Any,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    number = parse_number(value)
    if number is None:
        return None
    if minimum is not None and number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    return number


def _valid_bp_pair(systolic: Any, diastolic: Any) -> tuple[float, float] | None:
    normalized_systolic = _valid_number(systolic, 60, 300)
    normalized_diastolic = _valid_number(diastolic, 30, 200)
    if (
        normalized_systolic is None
        or normalized_diastolic is None
        or normalized_systolic <= normalized_diastolic
    ):
        return None
    return normalized_systolic, normalized_diastolic


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


def _truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return _clean_text(value).casefold() in {"1", "true", "yes", "да"}


def _visit_identity(visit: Mapping[str, Any]) -> tuple[str, ...]:
    visit_id = _clean_text(
        _first(visit, "id_priema", "visit_id", "appointment_id", "id")
    )
    if visit_id:
        canonical_id = re.sub(r"[_-]dup(?:licate)?$", "", visit_id, flags=re.IGNORECASE)
        return ("id", canonical_id.casefold())

    doctor = _as_mapping(_first(visit, "VRACH", "vrach", "doctor", "physician"))
    diagnosis = _as_mapping(
        _first(visit, "diagnoz_priema", "diagnosis", "diagnoz", "visit_diagnosis")
    )
    return (
        "content",
        normalize_date(
            _first(visit, "dt_priem", "date", "visit_date", "DATA_PRIEMA")
        )
        or "",
        _clean_text(_first(doctor, "fio_doc", "FIO", "fio", "name")).casefold(),
        _clean_text(
            _first(diagnosis, "osnovnoy_txt", "diagnosis", "diagnoz", "name")
        ).casefold(),
        _clean_text(
            _first(visit, "JALOBY_TXT", "jaloby_txt", "complaints", "jaloby")
        ).casefold(),
    )


def _unique_visits(source: Any) -> list[Mapping[str, Any]]:
    selected: dict[
        tuple[str, ...], tuple[int, tuple[int, bool], Mapping[str, Any]]
    ] = {}
    order: list[tuple[str, ...]] = []
    for index, visit in enumerate(_records(source)):
        identity = _visit_identity(visit)
        quality = _visit_quality(visit)
        current = selected.get(identity)
        if current is None:
            order.append(identity)
            selected[identity] = (index, quality, visit)
        elif quality > current[1]:
            merged = _merge_missing(visit, current[2])
            selected[identity] = (
                current[0],
                (_completeness_score(merged), quality[1] or current[1][1]),
                merged,
            )
        else:
            merged = _merge_missing(current[2], visit)
            selected[identity] = (
                current[0],
                (_completeness_score(merged), current[1][1] or quality[1]),
                merged,
            )
    return [selected[identity][2] for identity in order]


def _visit_quality(visit: Mapping[str, Any]) -> tuple[int, bool]:
    visit_id = _clean_text(
        _first(visit, "id_priema", "visit_id", "appointment_id", "id")
    )
    is_original = not bool(
        re.search(r"[_-]dup(?:licate)?$", visit_id, flags=re.IGNORECASE)
    )
    return _completeness_score(visit), is_original


def _completeness_score(value: Any) -> int:
    if isinstance(value, Mapping):
        return sum(_completeness_score(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return sum(_completeness_score(item) for item in value)
    return int(_has_value(value))


def _merge_missing(preferred: Any, fallback: Any) -> Any:
    if isinstance(preferred, Mapping) and isinstance(fallback, Mapping):
        result = dict(preferred)
        for key, fallback_value in fallback.items():
            if key in result:
                result[key] = _merge_missing(result[key], fallback_value)
            else:
                result[key] = fallback_value
        return result
    if isinstance(preferred, list) and isinstance(fallback, list):
        result = list(preferred)
        for item in fallback:
            if item not in result:
                result.append(item)
        return result
    return preferred if _has_value(preferred) else fallback


def _deduplicate(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


__all__ = [
    "MISParser",
    "PROFILE_FIELDS",
    "VITALS_FIELDS",
    "VISITS_FIELDS",
    "extract_vitals_from_text",
    "normalize_date",
    "normalize_number",
    "parse_date",
    "parse_number",
]
