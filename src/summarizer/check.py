"""Minimal end-to-end check for local Gemini credentials and structured output."""

from __future__ import annotations

from .client import GeminiSummaryClient
from .config import SummarySettings
from .errors import SummarizerError
from .models import ContextFact, SummaryContext


def main() -> int:
    """Send one synthetic fact through the same client used by the dashboard."""

    settings = SummarySettings.from_env()
    try:
        client = GeminiSummaryClient.from_settings(settings)
        client.generate(
            SummaryContext(
                facts=[
                    ContextFact(
                        source_id="condition:key-check",
                        kind="condition",
                        text="диагноз: тестовая запись для проверки подключения",
                    )
                ]
            )
        )
    except SummarizerError as error:
        print(f"Ошибка: {error}")
        return 1

    print(
        f"Ключ работает: модель {settings.model} вернула валидный structured output."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
