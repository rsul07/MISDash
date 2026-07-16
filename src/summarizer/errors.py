"""Stable errors exposed by the summarizer boundary."""


class SummarizerError(RuntimeError):
    """Base error safe for the application layer to handle."""


class MissingApiKeyError(SummarizerError):
    """Gemini cannot be called because no API key is configured."""


class InsufficientClinicalDataError(SummarizerError):
    """No facts are available, so an API request would be pointless."""


class InvalidSummaryError(SummarizerError):
    """The provider response is invalid or has no traceable statements."""


class SummaryProviderError(SummarizerError):
    """The external model request failed."""
