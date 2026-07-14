"""Canonical adapters for procedures, admissions, vaccines and reports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.contracts.v1 import (
    DiagnosticReport,
    Hospitalization,
    Immunization,
    Procedure,
)
from src.contracts.v1.common import Coding

from ..normalizers import clean_text
from ..records import first, records, truthy_flag
from .common import event_id, original_date_text, source_reference
from .dates import parse_clinical_date


@dataclass(frozen=True)
class HistoryBundle:
    procedures: list[Procedure]
    hospitalizations: list[Hospitalization]
    immunizations: list[Immunization]
    diagnostic_reports: list[DiagnosticReport]


def build_history(data: Mapping[str, Any]) -> HistoryBundle:
    return HistoryBundle(
        procedures=_build_procedures(data),
        hospitalizations=_build_hospitalizations(data),
        immunizations=_build_immunizations(data),
        diagnostic_reports=_build_instrumental_reports(data),
    )


def _build_procedures(data: Mapping[str, Any]) -> list[Procedure]:
    source = first(data, "perenesennye_operacii", "procedures", "operations")
    result: list[Procedure] = []
    for index, item in enumerate(records(source)):
        note = clean_text(first(item, "prim", "note", "comment"))
        if "дубл" in note.casefold() or truthy_flag(first(item, "is_deleted", "deleted")):
            continue
        display = clean_text(first(item, "operaciya", "OPER_NAME", "procedure", "name"))
        if not display:
            continue
        raw_date = first(item, "data", "DATA_OPER", "performed_at", "date")
        performed_at = parse_clinical_date(raw_date)
        result.append(
            Procedure(
                id=event_id("procedure", index, first(item, "id", "procedure_id")),
                source=source_reference("perenesennye_operacii", index),
                coding=Coding(display=display),
                performed_at=performed_at,
                performed_at_text=original_date_text(raw_date, performed_at),
                facility=clean_text(first(item, "lpu", "facility")) or None,
                outcome=clean_text(first(item, "oslojneniya", "outcome")) or None,
                note=note or None,
            )
        )
    return result


def _build_hospitalizations(data: Mapping[str, Any]) -> list[Hospitalization]:
    source = first(data, "gospitalizacii", "hospitalizations", "admissions")
    result: list[Hospitalization] = []
    for index, item in enumerate(records(source)):
        admitted_raw = first(item, "postuplenie", "admitted_at", "admission_date")
        discharged_raw = first(item, "vypiska", "discharged_at", "discharge_date")
        admitted_at = parse_clinical_date(admitted_raw)
        discharged_at = parse_clinical_date(discharged_raw)
        code = clean_text(first(item, "MKB10", "code", "icd10"))
        display = clean_text(first(item, "diagnoz_zaklyuch", "diagnosis"))
        result.append(
            Hospitalization(
                id=event_id("hospitalization", index, first(item, "id", "admission_id")),
                source=source_reference("gospitalizacii", index),
                facility=clean_text(first(item, "lpu", "facility")) or None,
                admitted_at=admitted_at,
                admitted_at_text=original_date_text(admitted_raw, admitted_at),
                discharged_at=discharged_at,
                discharged_at_text=original_date_text(discharged_raw, discharged_at),
                diagnosis=Coding(
                    code=code or None,
                    display=display or code,
                    system="ICD-10" if code else None,
                )
                if display or code
                else None,
                outcome=clean_text(first(item, "ishod", "outcome")) or None,
            )
        )
    return result


def _build_immunizations(data: Mapping[str, Any]) -> list[Immunization]:
    source = first(data, "privivki", "immunizations", "vaccinations")
    result: list[Immunization] = []
    for index, item in enumerate(records(source)):
        vaccine = clean_text(first(item, "vakcina", "vaccine", "name"))
        if not vaccine:
            continue
        raw_date = first(item, "data", "administered_at", "date")
        administered_at = parse_clinical_date(raw_date)
        result.append(
            Immunization(
                id=event_id("immunization", index, first(item, "id", "immunization_id")),
                source=source_reference("privivki", index),
                vaccine=vaccine,
                administered_at=administered_at,
                administered_at_text=original_date_text(raw_date, administered_at),
                lot_number=clean_text(first(item, "seriya", "lot_number")) or None,
            )
        )
    return result


def _build_instrumental_reports(data: Mapping[str, Any]) -> list[DiagnosticReport]:
    source = first(
        data,
        "instrumental_issled",
        "instrumental_reports",
        "diagnostic_reports",
    )
    result: list[DiagnosticReport] = []
    for index, item in enumerate(records(source)):
        display = clean_text(first(item, "issledovanie", "study", "name"))
        if not display:
            continue
        source_id = first(item, "protokol_id", "report_id", "id")
        raw_date = first(item, "DT_ISSLED", "effective_at", "date")
        effective_at = parse_clinical_date(raw_date)
        result.append(
            DiagnosticReport(
                id=event_id("instrumental-report", index, source_id),
                source=source_reference("instrumental_issled", index, source_id),
                category="instrumental",
                coding=Coding(display=display),
                effective_at=effective_at,
                effective_at_text=original_date_text(raw_date, effective_at),
                conclusion=clean_text(
                    first(item, "zakluchenie_txt", "conclusion", "result")
                )
                or None,
                performer=clean_text(first(item, "vrach_fd", "performer", "doctor"))
                or None,
                status=clean_text(first(item, "status", "report_status")) or None,
            )
        )
    return result
