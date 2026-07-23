"""Derived values from a single standard lipid panel."""

from __future__ import annotations

from .models import CalculatorDefinition
from .validation import non_negative_number, positive_number


CHOLESTEROL_MG_DL_PER_MMOL_L = 38.67
TRIGLYCERIDES_MG_DL_PER_MMOL_L = 88.57
SAMPSON_MAX_TRIGLYCERIDES_MG_DL = 800.0

NON_HDL_CHOLESTEROL = CalculatorDefinition(
    code="non-hdl-cholesterol",
    display="Холестерин не-ЛПВП",
    unit="mmol/L",
    description=(
        "Холестерин всех атерогенных apoB-содержащих частиц: общий холестерин "
        "за вычетом холестерина ЛПВП."
    ),
    inputs=("Общий холестерин", "Холестерин ЛПВП из той же липидограммы"),
    purpose=(
        "Дополняет ЛПНП при оценке атерогенных липопротеинов, в том числе при "
        "диабете и повышенных триглицеридах."
    ),
    method="Non-HDL-C = total cholesterol - HDL-C",
    standard=(
        "Используется в ESC/EAS 2019 с focused update 2025 и ACC/AHA 2026 "
        "как показатель атерогенного холестерина"
    ),
    limitations=(
        "Компоненты должны относиться к одной пробе и иметь совместимые единицы.",
        "Целевое значение зависит от общего сердечно-сосудистого риска.",
        "Показатель не заменяет клиническую оценку или измерение apoB.",
    ),
    references=(
        "https://doi.org/10.1093/eurheartj/ehz455",
        "https://academic.oup.com/eurheartj/article/46/42/4359/8234482",
        "https://doi.org/10.1161/CIR.0000000000001423",
    ),
)

SAMPSON_LDL_CHOLESTEROL = CalculatorDefinition(
    code="calculated-ldl-cholesterol",
    display="Расчётный холестерин ЛПНП (Sampson)",
    unit="mmol/L",
    description=(
        "Оценка холестерина ЛПНП по общему холестерину, ЛПВП и триглицеридам, "
        "когда прямого результата ЛПНП в липидограмме нет."
    ),
    inputs=(
        "Общий холестерин",
        "Холестерин ЛПВП из той же липидограммы",
        "Триглицериды из той же липидограммы",
    ),
    purpose=(
        "Восстанавливает отсутствующий показатель ЛПНП без подмены прямого "
        "лабораторного результата."
    ),
    method="Sampson-NIH equation 2 (2020)",
    standard=(
        "Sampson/NIH — один из методов, предпочитаемых ACC/AHA 2026 формуле "
        "Friedewald для расчётного ЛПНП"
    ),
    limitations=(
        "Результат всегда должен быть помечен как расчётный.",
        "Не рассчитывается при триглицеридах выше 800 mg/dL (около 9 mmol/L).",
        "Прямой ЛПНП из той же пробы имеет приоритет.",
        "Не применяется при неизвестных единицах или неполной липидограмме.",
    ),
    references=(
        "https://doi.org/10.1001/jamacardio.2020.0013",
        "https://doi.org/10.1161/CIR.0000000000001423",
    ),
)


def calculate_non_hdl_cholesterol(
    *,
    total_cholesterol: float,
    hdl_cholesterol: float,
) -> float:
    """Calculate non-HDL cholesterol with both inputs in the same unit."""

    total = positive_number(total_cholesterol, name="total_cholesterol")
    hdl = non_negative_number(hdl_cholesterol, name="hdl_cholesterol")
    if hdl > total:
        raise ValueError("hdl_cholesterol must not exceed total_cholesterol")
    return total - hdl


def calculate_sampson_ldl_cholesterol(
    *,
    total_cholesterol_mg_dl: float,
    hdl_cholesterol_mg_dl: float,
    triglycerides_mg_dl: float,
) -> float:
    """Calculate LDL-C in mg/dL using Sampson-NIH equation 2 (2020)."""

    total = positive_number(
        total_cholesterol_mg_dl,
        name="total_cholesterol_mg_dl",
    )
    hdl = non_negative_number(
        hdl_cholesterol_mg_dl,
        name="hdl_cholesterol_mg_dl",
    )
    triglycerides = non_negative_number(
        triglycerides_mg_dl,
        name="triglycerides_mg_dl",
    )
    if hdl > total:
        raise ValueError("hdl_cholesterol_mg_dl must not exceed total cholesterol")
    if triglycerides > SAMPSON_MAX_TRIGLYCERIDES_MG_DL:
        raise ValueError("Sampson equation is not validated above 800 mg/dL TG")

    non_hdl = total - hdl
    ldl = (
        total / 0.948
        - hdl / 0.971
        - (
            triglycerides / 8.56
            + triglycerides * non_hdl / 2140
            - triglycerides**2 / 16100
        )
        - 9.44
    )
    if ldl < 0:
        raise ValueError("Sampson equation produced a negative LDL result")
    return ldl
