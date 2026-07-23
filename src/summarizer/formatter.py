"""Deterministic Markdown rendering for DashboardResponse.ai_summary."""

from __future__ import annotations

from src.contracts.summarizer.v1 import ClinicalSummary, SummaryItem


_SECTIONS = (
    ("Что изменилось", "recent_changes"),
    ("Неочевидные находки", "important_findings"),
    ("Нерешённые вопросы", "unresolved_issues"),
    ("К ближайшему приёму", "next_visit_focus"),
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
