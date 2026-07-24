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
    assert streamlit.markdown.call_args.kwargs["unsafe_allow_html"] is True


def test_source_status_escapes_filename(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(theme, "st", streamlit)

    theme.render_source_status(filename="<patient>.json", origin="upload")

    html = streamlit.markdown.call_args.args[0]
    assert "<patient>" not in html
    assert "&lt;patient&gt;.json" in html
    assert "загруженный JSON" in html
