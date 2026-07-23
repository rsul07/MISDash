"""Race-free 2021 CKD-EPI creatinine equation for adults."""

from __future__ import annotations

from .models import CalculatorDefinition
from .validation import positive_number


EGFR_CKD_EPI_2021 = CalculatorDefinition(
    code="egfr-ckd-epi-2021",
    display="Расчётная СКФ (CKD-EPI 2021)",
    unit="mL/min/1.73m2",
    description=(
        "Оценка скорости клубочковой фильтрации по сывороточному креатинину, "
        "возрасту и полу без расового коэффициента."
    ),
    inputs=("Сывороточный креатинин", "Возраст на дату анализа", "Пол"),
    purpose=(
        "Показывает динамику расчётной функции почек и помогает заметить "
        "изменения, требующие клинической оценки."
    ),
    method="2021 CKD-EPI creatinine equation",
    standard=(
        "CKD-EPI 2021; приведено KDIGO 2024 среди валидированных "
        "уравнений для взрослых"
    ),
    limitations=(
        "Применяется только с 18 лет.",
        "Это оценка, а не прямое измерение функции почек.",
        "Точность снижается при нестабильном креатинине и необычной мышечной массе.",
        "Одно значение не устанавливает диагноз хронической болезни почек.",
        "Клинические ограничения формулы backend автоматически не определяет.",
    ),
    references=(
        "https://www.niddk.nih.gov/research-funding/research-programs/"
        "kidney-clinical-research-epidemiology/laboratory/"
        "glomerular-filtration-rate-equations/adults",
        "https://kdigo.org/wp-content/uploads/2024/03/"
        "KDIGO-2024-CKD-Guideline.pdf",
        "https://doi.org/10.1056/NEJMoa2102953",
    ),
)


def calculate_egfr_ckd_epi_2021(
    *,
    creatinine: float,
    creatinine_unit: str,
    age: int,
    sex: str,
) -> float:
    """Calculate adult eGFR using the race-free 2021 CKD-EPI equation.

    Creatinine may be supplied in ``mg/dL`` or ``µmol/L``. The returned value
    is in mL/min/1.73m². No clinical category or diagnosis is inferred.
    """

    if age < 18:
        raise ValueError("2021 CKD-EPI creatinine equation requires age >= 18")
    if sex not in {"female", "male"}:
        raise ValueError("sex must be 'female' or 'male'")

    serum_creatinine = positive_number(creatinine, name="creatinine")
    unit = _normalize_creatinine_unit(creatinine_unit)
    if unit == "µmol/L":
        serum_creatinine /= 88.4

    if sex == "female":
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0

    ratio = serum_creatinine / kappa
    return (
        142
        * min(ratio, 1) ** alpha
        * max(ratio, 1) ** -1.2
        * 0.9938**age
        * sex_factor
    )


def _normalize_creatinine_unit(unit: str) -> str:
    normalized = unit.casefold().replace(" ", "").replace("μ", "µ")
    aliases = {
        "mg/dl": "mg/dL",
        "мг/дл": "mg/dL",
        "µmol/l": "µmol/L",
        "umol/l": "µmol/L",
        "мкмоль/л": "µmol/L",
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(f"unsupported creatinine unit: {unit}") from error
