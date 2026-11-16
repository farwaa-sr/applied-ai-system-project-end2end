from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def fresh() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.sidebar.checkbox[0].set_value(True).run()  # offline: no network in tests
    return at


def test_app_loads_with_five_questions():
    at = fresh()
    assert not at.exception
    assert len(at.radio) == 5


def test_submitting_all_answers_shows_five_recommendations():
    at = fresh()
    for radio, choice in zip(at.radio, ["a", "a", "b", "a", "a"]):
        radio.set_value(choice)
    at.button[0].click().run()
    assert not at.exception
    assert not at.error
    assert any("Recommendations" in s.value for s in at.subheader)
    assert len([m for m in at.markdown if m.value.startswith("**") and "—" in m.value]) == 5


def test_missing_answers_show_friendly_error():
    at = fresh()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.error) == 1
