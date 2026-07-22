"""Build derived lipids from components of one laboratory report."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from src.calculators import (
    CalculatedValue,
    CalculationInput,
    NON_HDL_CHOLESTEROL,
    SAMPSON_LDL_CHOLESTEROL,
    calculate_non_hdl_cholesterol,
    calculate_sampson_ldl_cholesterol,
)
from src.calculators.lipids import (
    CHOLESTEROL_MG_DL_PER_MMOL_L,
    TRIGLYCERIDES_MG_DL_PER_MMOL_L,
)
from src.contracts.patient.v1 import Observation, PatientRecord

from ..measurements import metric_code, normalize_unit


def calculate_lipid_metrics(record: PatientRecord) -> list[CalculatedValue]:
    """Calculate non-HDL and missing LDL without crossing report boundaries."""

    panels: dict[str, list[Observation]] = defaultdict(list)
    for observation in record.observations:
        if observation.category == "laboratory" and observation.report_id:
            panels[observation.report_id].append(observation)

    values: list[CalculatedValue] = []
    for panel in panels.values():
        by_code: dict[str, list[Observation]] = defaultdict(list)
        for observation in panel:
            code = metric_code(observation.coding)
            if code is not None:
                by_code[code].append(observation)

        total = _single_lipid(by_code["total-cholesterol"], "total-cholesterol")
        hdl = _single_lipid(by_code["hdl-cholesterol"], "hdl-cholesterol")
        if total is None or hdl is None:
            continue
        total_observation, total_value = total
        hdl_observation, hdl_value = hdl
        observed_at = _same_observed_at(total_observation, hdl_observation)
        if observed_at is None:
            continue
        try:
            non_hdl = calculate_non_hdl_cholesterol(
                total_cholesterol=total_value,
                hdl_cholesterol=hdl_value,
            )
        except ValueError:
            continue
        values.append(
            CalculatedValue(
                definition=NON_HDL_CHOLESTEROL,
                observed_at=observed_at,
                value=round(non_hdl, 3),
                source_ids=(total_observation.id, hdl_observation.id),
                inputs=(
                    _calculation_input(
                        "Общий холестерин", total_value, total_observation
                    ),
                    _calculation_input(
                        "Холестерин ЛПВП", hdl_value, hdl_observation
                    ),
                ),
            )
        )

        if _has_usable_lipid(by_code["ldl-cholesterol"], "ldl-cholesterol"):
            continue
        triglycerides = _single_lipid(
            by_code["triglycerides"],
            "triglycerides",
        )
        if triglycerides is None:
            continue
        triglycerides_observation, triglycerides_value = triglycerides
        observed_at = _same_observed_at(
            total_observation,
            hdl_observation,
            triglycerides_observation,
        )
        if observed_at is None:
            continue
        estimated_ldl = _estimate_ldl(
            total_value,
            hdl_value,
            triglycerides_value,
        )
        if estimated_ldl is None:
            continue
        values.append(
            CalculatedValue(
                definition=SAMPSON_LDL_CHOLESTEROL,
                observed_at=observed_at,
                value=round(estimated_ldl, 3),
                source_ids=(
                    total_observation.id,
                    hdl_observation.id,
                    triglycerides_observation.id,
                ),
                inputs=(
                    _calculation_input(
                        "Общий холестерин", total_value, total_observation
                    ),
                    _calculation_input(
                        "Холестерин ЛПВП", hdl_value, hdl_observation
                    ),
                    _calculation_input(
                        "Триглицериды",
                        triglycerides_value,
                        triglycerides_observation,
                    ),
                ),
            )
        )
    return values


def _calculation_input(
    display: str,
    value: float,
    observation: Observation,
) -> CalculationInput:
    return CalculationInput(
        display=display,
        value=value,
        unit="mmol/L",
        source_id=observation.id,
    )


def _estimate_ldl(
    total_mmol_l: float,
    hdl_mmol_l: float,
    triglycerides_mmol_l: float,
) -> float | None:
    try:
        result_mg_dl = calculate_sampson_ldl_cholesterol(
            total_cholesterol_mg_dl=(
                total_mmol_l * CHOLESTEROL_MG_DL_PER_MMOL_L
            ),
            hdl_cholesterol_mg_dl=(
                hdl_mmol_l * CHOLESTEROL_MG_DL_PER_MMOL_L
            ),
            triglycerides_mg_dl=(
                triglycerides_mmol_l * TRIGLYCERIDES_MG_DL_PER_MMOL_L
            ),
        )
    except ValueError:
        return None
    return result_mg_dl / CHOLESTEROL_MG_DL_PER_MMOL_L


def _single_lipid(
    observations: list[Observation],
    code: str,
) -> tuple[Observation, float] | None:
    usable: list[tuple[Observation, float]] = []
    for observation in observations:
        if observation.value is None or not isinstance(
            observation.value.value,
            (int, float),
        ):
            continue
        value = _lipid_value_mmol_l(
            float(observation.value.value),
            observation.value.unit,
            code,
        )
        if value is not None:
            usable.append((observation, value))
    return usable[0] if len(usable) == 1 else None


def _has_usable_lipid(observations: list[Observation], code: str) -> bool:
    for observation in observations:
        if observation.value is None or not isinstance(
            observation.value.value,
            (int, float),
        ):
            continue
        if (
            _lipid_value_mmol_l(
                float(observation.value.value),
                observation.value.unit,
                code,
            )
            is not None
        ):
            return True
    return False


def _lipid_value_mmol_l(
    value: float,
    unit: str | None,
    code: str,
) -> float | None:
    normalized_unit = normalize_unit(unit)
    if normalized_unit == "mmol/L":
        return value
    if normalized_unit != "mg/dL":
        return None
    factor = (
        TRIGLYCERIDES_MG_DL_PER_MMOL_L
        if code == "triglycerides"
        else CHOLESTEROL_MG_DL_PER_MMOL_L
    )
    return value / factor


def _same_observed_at(
    *observations: Observation,
) -> date | datetime | None:
    observed_at = [item.observed_at for item in observations]
    first = observed_at[0]
    if first is None or any(item != first for item in observed_at[1:]):
        return None
    return first
