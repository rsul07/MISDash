"""Deterministic Markdown rendering for DashboardResponse.ai_summary."""

from __future__ import annotations

from .models import ClinicalSummary, SummaryItem


_SECTIONS = (
    ("Диагнозы", "diagnoses"),
    ("Текущая терапия", "therapy"),
    ("Динамика", "dynamics"),
    ("Важно на ближайшем приёме", "next_visit_priorities"),
)


def format_summary(summary: ClinicalSummary) -> str:
    """Render only clinician-facing text; source IDs remain in typed result."""

    sections: list[str] = []
    for title, field_name in _SECTIONS:
        items: list[SummaryItem] = getattr(summary, field_name)
        if not items:
            continue
        body = "\n".join(f"- {item.text}" for item in items)
        sections.append(f"### {title}\n\n{body}")
    return "\n\n".join(sections)
