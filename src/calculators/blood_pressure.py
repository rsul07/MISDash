"""Derived values from a single paired blood-pressure measurement."""

from __future__ import annotations

from .models import CalculatorDefinition
from .validation import positive_number


PULSE_PRESSURE = CalculatorDefinition(
    code="pulse-pressure",
    display="Пульсовое давление",
    unit="mmHg",
    description=(
        "Разница между систолическим и диастолическим давлением в одном "
        "измерении."
    ),
    inputs=("Систолическое АД", "Диастолическое АД из того же измерения"),
    purpose=(
        "Показывает динамику амплитуды давления; расширение показателя с "
        "возрастом может сопровождать снижение эластичности крупных артерий."
    ),
    method="Pulse pressure = systolic BP - diastolic BP",
    standard=(
        "Связь пульсового давления с возрастным аортальным уплотнением "
        "описана в ESC 2024 по артериальной гипертензии"
    ),
    limitations=(
        "Это косвенный показатель, а не измерение жёсткости артерий.",
        "Для оценки жёсткости сосудов применяют скорость пульсовой волны.",
        "Не используется здесь как самостоятельный порог или красный флаг.",
        "САД и ДАД должны относиться к одному измерению.",
    ),
    references=(
        "https://academic.oup.com/eurheartj/article/45/38/3912/7741010",
    ),
)


def calculate_pulse_pressure(*, systolic: float, diastolic: float) -> float:
    """Calculate pulse pressure in mmHg from one paired BP measurement."""

    systolic_value = positive_number(systolic, name="systolic")
    diastolic_value = positive_number(diastolic, name="diastolic")
    if systolic_value <= diastolic_value:
        raise ValueError("systolic must be greater than diastolic")
    return systolic_value - diastolic_value
