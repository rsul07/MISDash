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

    theme.render_source_status(filename="<patient>.json", origin="upload")

    html = streamlit.markdown.call_args.args[0]
    assert "<patient>" not in html
    assert "&lt;patient&gt;.json" in html
    assert "загруженный JSON" in html


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
