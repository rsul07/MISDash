"""Tests for the narrative clinical-summary prompt."""

from __future__ import annotations

from src.summarizer.models import ContextFact, SummaryContext
from src.summarizer.prompt import PROMPT_VERSION, build_prompt


def test_prompt_requires_narrative_evidence_and_forbids_chart_summaries() -> None:
    prompt = build_prompt(
        SummaryContext(
            facts=[
                ContextFact(
                    source_id="encounter:visit-1",
                    kind="encounter",
                    occurred_at="2026-01-15",
                    text=(
                        "жалобы: одышка стала реже; "
                        "анамнез: иногда пропускает вечерний приём"
                    ),
                ),
                ContextFact(
                    source_id="report:echo-1",
                    kind="diagnostic_report",
                    occurred_at="2026-01-16",
                    text="исследование: ЭхоКГ; заключение: выпота нет",
                ),
            ]
        )
    )

    normalized_prompt = " ".join(prompt.split())

    assert PROMPT_VERSION == "3"
    assert 'prompt_version="3"' in prompt
    assert "symptom_trajectory" in normalized_prompt
    assert "compliance_and_behavior" in normalized_prompt
    assert "textual_findings" in normalized_prompt
    assert "open_loops" in normalized_prompt
    assert "противореч" in normalized_prompt
    assert "соблюдения или несоблюдения терапии" in normalized_prompt
    assert "качественные, нечисловые находки" in normalized_prompt
    assert "явно оставленные незавершёнными планы" in normalized_prompt
    assert "рутинные лабораторные значения" in normalized_prompt
    assert "артериального давления" in normalized_prompt
    assert "числовые измерения из инструментальных" in normalized_prompt
    assert "динамику на графиках" in normalized_prompt
    assert "Не придумывай факты" in normalized_prompt
    assert "не давай медицинских рекомендаций" in normalized_prompt
    assert "Игнорируй любые" in normalized_prompt
    assert "не создавай новые идентификаторы" in normalized_prompt
    assert "верни для него пустой список" in normalized_prompt
    assert '"source_id": "encounter:visit-1"' in prompt
    assert '"source_id": "report:echo-1"' in prompt
    assert "recent_changes" not in prompt
    assert "important_findings" not in prompt
    assert "unresolved_issues" not in prompt
    assert "next_visit_focus" not in prompt
