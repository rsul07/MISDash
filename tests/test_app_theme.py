"""Tests for the local, offline-safe visual system."""

from unittest.mock import MagicMock

from src.app import theme


def test_theme_uses_presentation_palette_and_reduced_motion(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.apply_app_theme()

    css = streamlit.markdown.call_args.args[0]
    assert theme.NAVY in css
    assert theme.BLUE in css
    assert theme.TEAL in css
    assert theme.AMBER in css
    assert "prefers-reduced-motion: reduce" in css
    assert "mis-fade-up" in css
    assert '[data-testid="stHeaderActionElements"]' in css
    assert "display: none !important;" in css
    assert streamlit.markdown.call_args.kwargs["unsafe_allow_html"] is True


def test_source_status_escapes_filename(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.render_source_status(filename="<patient>.json")

    html = streamlit.markdown.call_args.args[0]
    assert "<patient>" not in html
    assert "&lt;patient&gt;.json" in html
    assert "Файл обработан" in html
    assert "данные обработаны" not in html


def test_sidebar_action_buttons_have_readable_resting_state(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.apply_app_theme()

    css = streamlit.markdown.call_args.args[0]
    assert '[data-testid="stFileUploader"] button span' in css
    assert '[data-testid="stFileUploader"] button p' in css
    assert "color: var(--mis-navy) !important;" in css
    assert '[data-testid="stDownloadButton"] button {' in css
    assert "background: var(--mis-action);" in css
    assert '[data-testid="stDownloadButton"] button p' in css
    assert '[data-testid="stNumberInputStepDown"]' in css
    assert '[data-testid="stNumberInputStepUp"]' in css
    assert '[data-testid="InputInstructions"]' in css


def test_headers_do_not_render_decorative_eyebrows(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.render_sidebar_header()
    theme.render_empty_state()
    theme.render_section_header("Пациент")

    rendered = "\n".join(
        call.args[0] for call in streamlit.markdown.call_args_list
    )
    assert "mis-eyebrow" not in rendered
    assert "КЛИНИЧЕСКАЯ СВОДКА" not in rendered
    assert "НАЧАЛО РАБОТЫ" not in rendered
    assert "ИСТОЧНИК ДАННЫХ" not in rendered
    assert "Демонстрационный контур" not in rendered
    assert "mis-sidebar-logo" not in rendered
    assert "mis-app-mark" not in rendered
    assert "mis-empty-icon" not in rendered
    assert rendered.count("MIS Dash") == 1
    assert "JSON-файл пациента" in rendered
    section_html = streamlit.markdown.call_args.args[0]
    assert "<h2>Пациент</h2>" in section_html
    assert "<p>" not in section_html


def test_patient_card_centers_columns_and_stat_values(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.apply_app_theme()

    css = streamlit.markdown.call_args.args[0]
    assert ":has(.mis-patient-marker)" in css
    assert '[data-testid="stHorizontalBlock"]:has(.mis-patient-marker)' in css
    assert "grid-template-rows: minmax(1.4rem, auto) 1fr;" in css
    assert "align-items: center !important;" in css


def test_red_flag_cards_prioritize_title_and_explanation(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.apply_app_theme()

    css = streamlit.markdown.call_args.args[0]
    assert ".mis-flag-heading" in css
    assert "font-size: 0.9rem;" in css
    assert "line-height: 1.55;" in css


def test_calculated_metric_card_has_distinct_visual_treatment(
    monkeypatch,
) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.apply_app_theme()

    css = streamlit.markdown.call_args.args[0]
    assert ".mis-latest-value--calculated" in css
    assert "inset 0.2rem 0 0 var(--mis-teal)" in css


def test_mobile_layout_uses_touch_targets_and_card_grids(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.apply_app_theme()

    css = streamlit.markdown.call_args.args[0]
    assert "@media (max-width: 720px)" in css
    assert 'grid-template-columns: repeat(6, minmax(0, 1fr));' in css
    assert '[data-testid="stColumn"]:nth-child(2)' in css
    assert '[data-testid="stColumn"]:nth-child(n + 4)' in css
    assert "grid-column: span 3;" in css
    assert "grid-column: span 2;" in css
    assert '[data-testid="stHorizontalBlock"]:has(.mis-patient-marker)' in css
    assert '[data-testid="stHorizontalBlock"]:has(.mis-latest-value)' in css
    assert ".mis-visit-table thead" in css
    assert "min-height: 2.75rem;" in css
