"""Build pulse pressure from atomic blood-pressure observations."""

from __future__ import annotations

from collections import defaultdict

from src.calculators import (
    CalculatedValue,
    PULSE_PRESSURE,
    calculate_pulse_pressure,
)
from src.contracts.patient.v1 import PatientRecord

from ..measurements import metric_code, normalize_unit


def calculate_pulse_pressure_metrics(
    record: PatientRecord,
) -> list[CalculatedValue]:
    """Calculate pulse pressure only from paired components of one event."""

    values: list[CalculatedValue] = []
    for observation in record.observations:
        if observation.observed_at is None:
            continue
        components: dict[str, list[float]] = defaultdict(list)
        for component in observation.components:
            code = metric_code(component.coding)
            quantity = component.value
            if (
                code not in {"systolic", "diastolic"}
                or not isinstance(quantity.value, (int, float))
                or normalize_unit(quantity.unit) != "mmHg"
            ):
                continue
            components[code].append(float(quantity.value))
        if len(components["systolic"]) != 1 or len(components["diastolic"]) != 1:
            continue
        try:
            pulse_pressure = calculate_pulse_pressure(
                systolic=components["systolic"][0],
                diastolic=components["diastolic"][0],
            )
        except ValueError:
            continue
        values.append(
            CalculatedValue(
                definition=PULSE_PRESSURE,
                observed_at=observation.observed_at,
                value=round(pulse_pressure, 2),
                source_ids=(observation.id,),
            )
        )
    return values
