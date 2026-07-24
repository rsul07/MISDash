"""Tests for top-level application configuration."""

from unittest.mock import MagicMock

from src.app import main


def test_page_configuration_has_no_training_copy(monkeypatch) -> None:
    streamlit = MagicMock()
    monkeypatch.setattr(main, "st", streamlit)
    monkeypatch.setattr(main, "apply_app_theme", MagicMock())
    monkeypatch.setattr(main, "render_sidebar_header", MagicMock())
    monkeypatch.setattr(main, "render_patient_source", MagicMock(return_value=None))
    monkeypatch.setattr(main, "render_empty_state", MagicMock())

    main.run_app()

    config = streamlit.set_page_config.call_args.kwargs
    assert config["page_title"] == "MIS Dash"
    assert "menu_items" not in config
