"""Public API for traceable clinical summaries."""

from .client import GeminiSummaryClient, SummaryClient
from .config import DEFAULT_GEMINI_MODEL, SummarySettings
from .context import ContextLimits, build_summary_context
from .errors import (
    InsufficientClinicalDataError,
    InvalidSummaryError,
    MissingApiKeyError,
    SummarizerError,
    SummaryProviderError,
)
from .formatter import format_summary
from .models import ClinicalSummary, ContextFact, SummaryContext, SummaryItem
from .service import SummaryService

__all__ = [
    "ClinicalSummary",
    "ContextFact",
    "ContextLimits",
    "DEFAULT_GEMINI_MODEL",
    "GeminiSummaryClient",
    "InsufficientClinicalDataError",
    "InvalidSummaryError",
    "MissingApiKeyError",
    "SummarizerError",
    "SummaryClient",
    "SummaryContext",
    "SummaryItem",
    "SummaryProviderError",
    "SummaryService",
    "SummarySettings",
    "build_summary_context",
    "format_summary",
]
