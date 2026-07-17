"""Provider boundary and Gemini implementation."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import ValidationError

from .config import SummarySettings
from .errors import InvalidSummaryError, MissingApiKeyError, SummaryProviderError
from .models import ClinicalSummary, SummaryContext
from .prompt import build_prompt


class SummaryClient(Protocol):
    def generate(self, context: SummaryContext) -> ClinicalSummary:
        """Generate one structured summary for the supplied facts."""


class GeminiSummaryClient:
    """Small adapter around the official Google Gen AI Python SDK."""

    def __init__(self, *, model: str, sdk_client: Any) -> None:
        self.model = model
        self._sdk_client = sdk_client

    @classmethod
    def from_settings(cls, settings: SummarySettings) -> "GeminiSummaryClient":
        if settings.api_key is None:
            raise MissingApiKeyError(
                "Не задан GEMINI_API_KEY. Добавьте ключ в локальный файл .env."
            )
        try:
            from google import genai
        except ImportError as error:  # pragma: no cover - installation failure
            raise SummaryProviderError(
                "Пакет google-genai не установлен. Установите зависимости проекта."
            ) from error
        return cls(
            model=settings.model,
            sdk_client=genai.Client(api_key=settings.api_key),
        )

    def generate(self, context: SummaryContext) -> ClinicalSummary:
        try:
            interaction = self._sdk_client.interactions.create(
                model=self.model,
                input=build_prompt(context),
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": ClinicalSummary.model_json_schema(),
                },
                store=False,
            )
        except Exception as error:
            raise _provider_error(error, self.model) from error

        output_text = getattr(interaction, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise InvalidSummaryError("Gemini вернул пустой ответ.")
        try:
            return ClinicalSummary.model_validate_json(output_text)
        except ValidationError as error:
            raise InvalidSummaryError(
                "Gemini вернул ответ, не соответствующий контракту сводки."
            ) from error


def _provider_error(error: Exception, model: str) -> SummaryProviderError:
    """Translate provider failures without exposing secrets or raw responses."""

    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    details = str(error).casefold()
    if status == 404 or "not_found" in details or "not found" in details:
        return SummaryProviderError(
            f"Модель Gemini '{model}' недоступна для этого проекта. "
            "Проверьте GEMINI_MODEL в .env."
        )
    if status in {400, 401, 403} and (
        "api key" in details or "permission" in details or status in {401, 403}
    ):
        return SummaryProviderError(
            "Gemini отклонил API-ключ или проект не имеет доступа к модели."
        )
    if status == 429 or "resource_exhausted" in details or "quota" in details:
        return SummaryProviderError(
            "Исчерпана квота Gemini API. Проверьте лимиты проекта в AI Studio."
        )
    return SummaryProviderError(
        "Не удалось выполнить запрос к Gemini API. Проверьте сеть и повторите позже."
    )
