"""Laboratory report and result observation adapter."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.contracts.v1 import DiagnosticReport, Observation

from ...normalizers import clean_text
from ...records import first, records, truthy_flag
from ..common import source_reference
from ..dates import parse_clinical_date
from .common import coding, quantity, reference_range


@dataclass(frozen=True)
class LaboratoryBundle:
    observations: list[Observation]
    reports: list[DiagnosticReport]


def build_laboratory(data: Mapping[str, Any]) -> LaboratoryBundle:
    source = first(data, "lab_issledovaniya", "laboratory_tests", "laboratory", "labs")
    observations: list[Observation] = []
    reports: list[DiagnosticReport] = []
    for panel_index, panel in enumerate(records(source)):
        source_id = first(panel, "nomer_zakaza", "order_id", "report_id", "id")
        report_id = clean_text(source_id) or f"laboratory-report-{panel_index + 1}"
        effective_at = parse_clinical_date(
            first(panel, "data_vzyatia", "collected_at", "date")
        )
        panel_observations = _panel_results(
            panel, panel_index, report_id, effective_at
        )
        observations.extend(panel_observations)
        group_code = clean_text(first(panel, "gruppa_issled", "group_code"))
        group_name = clean_text(
            first(panel, "gruppa_issled_name", "group_name", "name")
        )
        reports.append(
            DiagnosticReport(
                id=report_id,
                source=source_reference("lab_issledovaniya", panel_index, source_id),
                category="laboratory",
                coding=coding(
                    group_name or group_code or "Лабораторное исследование",
                    group_code or None,
                ),
                effective_at=effective_at,
                issued_at=parse_clinical_date(
                    first(panel, "data_gotovnosti", "issued_at", "ready_at")
                ),
                performer=clean_text(
                    first(panel, "vrach_kdl", "performer", "laboratory")
                )
                or None,
                facility=clean_text(
                    first(panel, "lab_otdelenie", "facility", "department")
                )
                or None,
                specimen=clean_text(
                    first(panel, "biomaterial", "specimen", "material")
                )
                or None,
                observation_ids=[item.id for item in panel_observations],
            )
        )
    return LaboratoryBundle(observations=observations, reports=reports)


def _panel_results(
    panel: Mapping[str, Any],
    panel_index: int,
    report_id: str,
    effective_at: Any,
) -> list[Observation]:
    source = first(panel, "REZULTATY", "rezultaty", "results", "indicators")
    result_records = records(source)
    if not result_records and first(panel, "pokazatel", "indicator", "test_name"):
        result_records = [panel]
    result: list[Observation] = []
    for index, item in enumerate(result_records):
        if truthy_flag(first(item, "is_deleted", "deleted")):
            continue
        display = clean_text(
            first(item, "pokazatel", "indicator", "test_name", "name")
        )
        if not display:
            continue
        source_id = first(item, "id_pokazatelya", "result_id", "id")
        code = clean_text(first(item, "kod_nsi", "code", "vneshniy_kod"))
        value = quantity(
            first(item, "REZULT", "REZULTAT", "result", "value", "znachenie"),
            first(item, "ed_izm", "unit", "units"),
        )
        result.append(
            Observation(
                id=f"{report_id}-result-{index + 1}",
                source=source_reference(
                    f"lab_issledovaniya[{panel_index}].REZULTATY", index, source_id
                ),
                observed_at=effective_at
                or parse_clinical_date(
                    first(item, "dt_validacii", "validated_at", "date")
                ),
                category="laboratory",
                coding=coding(display, code or None, "NSI" if code else None),
                value=value,
                reference_range=reference_range(
                    first(item, "referens", "reference_range", "reference")
                ),
                interpretation=clean_text(
                    first(item, "flag_H_L", "interpretation", "flag")
                )
                or None,
                method=clean_text(first(item, "metod", "method")) or None,
                status=clean_text(first(item, "status_rez", "status")) or None,
                report_id=report_id,
            )
        )
    return result
