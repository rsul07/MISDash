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
            raise SummaryProviderError(
                "Gemini API временно недоступен или исчерпана квота."
            ) from error

        output_text = getattr(interaction, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise InvalidSummaryError("Gemini вернул пустой ответ.")
        try:
            return ClinicalSummary.model_validate_json(output_text)
        except ValidationError as error:
            raise InvalidSummaryError(
                "Gemini вернул ответ, не соответствующий контракту сводки."
            ) from error
