"""Tests for selecting uploaded and generated MIS exports."""

from __future__ import annotations

from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest

from src.app import source
from src.generator import GenerationConfig


@pytest.fixture(autouse=True)
def clear_generator_cache() -> None:
    source._generate_json_bytes.clear()


def _streamlit(selected_source: str) -> MagicMock:
    streamlit = MagicMock()
    streamlit.session_state = {}
    streamlit.radio.return_value = selected_source
    streamlit.form.return_value = nullcontext()
    streamlit.number_input.return_value = 7
    streamlit.slider.return_value = 3
    streamlit.checkbox.return_value = True
    streamlit.spinner.return_value = nullcontext()
    return streamlit


def test_upload_source_returns_selected_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(source.UPLOAD_SOURCE)
    uploaded_file = MagicMock()
    uploaded_file.name = "../patient.json"
    uploaded_file.getvalue.return_value = b'{"patient": "uploaded"}'
    streamlit.file_uploader.return_value = uploaded_file
    monkeypatch.setattr(source, "st", streamlit)

    selected = source.render_patient_source()

    assert selected == source.PatientInput(
        file_bytes=b'{"patient": "uploaded"}',
        filename="patient.json",
        origin="upload",
    )
    streamlit.form.assert_not_called()
    streamlit.download_button.assert_not_called()


def test_empty_upload_source_shows_instruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(source.UPLOAD_SOURCE)
    streamlit.file_uploader.return_value = None
    monkeypatch.setattr(source, "st", streamlit)

    assert source.render_patient_source() is None
    streamlit.info.assert_called_once_with(
        "Загрузите JSON-файл пациента, чтобы сформировать дашборд."
    )


def test_generator_waits_for_explicit_submit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(source.GENERATED_SOURCE)
    streamlit.form_submit_button.return_value = False
    generate = MagicMock(return_value=b"{}")
    monkeypatch.setattr(source, "st", streamlit)
    monkeypatch.setattr(source, "generate_json_bytes", generate)

    assert source.render_patient_source() is None
    generate.assert_not_called()
    streamlit.button.assert_called_once_with(
        "Случайный seed",
        key=source._RANDOM_SEED_KEY,
        on_click=source._randomize_seed,
        width="stretch",
    )
    streamlit.download_button.assert_not_called()


def test_random_seed_button_only_replaces_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(source.GENERATED_SOURCE)
    monkeypatch.setattr(source, "st", streamlit)
    monkeypatch.setattr(source.secrets, "randbelow", MagicMock(return_value=123456))

    source._randomize_seed()

    assert streamlit.session_state[source._SEED_KEY] == 123456
    source.secrets.randbelow.assert_called_once_with(source._MAX_SEED + 1)


def test_generated_json_persists_without_repeated_generation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(source.GENERATED_SOURCE)
    streamlit.form_submit_button.side_effect = [True, False]
    generate = MagicMock(return_value=b'{"patient": "generated"}')
    monkeypatch.setattr(source, "st", streamlit)
    monkeypatch.setattr(source, "generate_json_bytes", generate)

    first = source.render_patient_source()
    second = source.render_patient_source()

    assert first == second == source.PatientInput(
        file_bytes=b'{"patient": "generated"}',
        filename="patient_seed_7_3y_light.json",
        origin="generated",
    )
    generate.assert_called_once_with(
        GenerationConfig(seed=7, years=3, light=True)
    )
    assert streamlit.download_button.call_count == 2
    captions = [call.args[0] for call in streamlit.caption.call_args_list]
    assert all("не уменьшает плотность дневников" not in text for text in captions)


def test_new_generator_parameters_replace_session_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(source.GENERATED_SOURCE)
    streamlit.form_submit_button.side_effect = [True, True]
    streamlit.number_input.side_effect = [7, 8]
    generate = MagicMock(side_effect=[b'{"seed": 7}', b'{"seed": 8}'])
    monkeypatch.setattr(source, "st", streamlit)
    monkeypatch.setattr(source, "generate_json_bytes", generate)

    first = source.render_patient_source()
    second = source.render_patient_source()

    assert first is not None
    assert first.filename == "patient_seed_7_3y_light.json"
    assert second == source.PatientInput(
        file_bytes=b'{"seed": 8}',
        filename="patient_seed_8_3y_light.json",
        origin="generated",
    )
    assert generate.call_count == 2


def test_stale_generated_session_state_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    streamlit = _streamlit(source.GENERATED_SOURCE)
    streamlit.form_submit_button.return_value = False
    streamlit.session_state[source._GENERATED_STATE_KEY] = {
        "file_bytes": b"{}",
        "filename": "old.json",
    }
    monkeypatch.setattr(source, "st", streamlit)

    assert source.render_patient_source() is None
    streamlit.download_button.assert_not_called()
