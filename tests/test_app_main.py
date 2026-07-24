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


def test_processed_file_notice_is_rendered_in_sidebar(monkeypatch) -> None:
    streamlit = MagicMock()
    patient_input = MagicMock(
        file_bytes=b'{"patient": "synthetic"}',
        filename="patient.json",
    )
    record = MagicMock()
    dashboard = MagicMock()
    source_status = MagicMock()
    dashboard_renderer = MagicMock()
    monkeypatch.setattr(main, "st", streamlit)
    monkeypatch.setattr(main, "apply_app_theme", MagicMock())
    monkeypatch.setattr(main, "render_sidebar_header", MagicMock())
    monkeypatch.setattr(
        main,
        "render_patient_source",
        MagicMock(return_value=patient_input),
    )
    monkeypatch.setattr(
        main,
        "build_pipeline",
        MagicMock(return_value=(record, dashboard)),
    )
    monkeypatch.setattr(main, "render_source_status", source_status)
    monkeypatch.setattr(main, "render_dashboard", dashboard_renderer)

    main.run_app()

    assert streamlit.sidebar.__enter__.call_count == 2
    source_status.assert_called_once_with(filename="patient.json")
    dashboard_renderer.assert_called_once_with(
        patient_input.file_bytes,
        record,
        dashboard,
    )
