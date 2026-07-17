"""Environment-backed summarizer configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"


@dataclass(frozen=True)
class SummarySettings:
    api_key: str | None = field(default=None, repr=False)
    model: str = DEFAULT_GEMINI_MODEL

    @classmethod
    def from_env(cls) -> "SummarySettings":
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
        model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        return cls(api_key=api_key, model=model or DEFAULT_GEMINI_MODEL)
