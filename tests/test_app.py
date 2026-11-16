import re
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app.py")
STUDY = ["a", "a", "b", "a", "b"]


def fresh() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.checkbox[0].set_value(True).run()  # offline: no network in tests
    return at


def answer(at: AppTest, letters) -> AppTest:
    for group, letter in zip(at.button_group, letters):
        group.set_value(letter)
    return at


def press(at: AppTest, label: str) -> AppTest:
    return next(b for b in at.button if label in b.label).click().run()


def titles(at: AppTest) -> list:
    html = " ".join(m.value for m in at.markdown)
    return re.findall(r'song-title">([^<]+)<', html)


def test_app_loads_with_five_question_groups():
    at = fresh()
    assert not at.exception
    assert len(at.button_group) == 5


def test_submitting_answers_shows_five_songs_and_actions():
    at = press(answer(fresh(), STUDY), "Find my music")
    assert not at.exception and not at.error
    assert len(titles(at)) == 5
    labels = " | ".join(b.label for b in at.button)
    assert "Show me new ones" in labels and "Start over" in labels


def test_missing_answers_show_friendly_error():
    at = press(fresh(), "Find my music")
    assert not at.exception
    assert len(at.error) == 1 and not titles(at)


def test_new_set_never_repeats_songs():
    at = press(answer(fresh(), STUDY), "Find my music")
    seen = titles(at)
    for expected_set in (2, 3):
        at = press(at, "Show me new ones")
        assert not at.exception
        now = titles(at)
        assert len(now) == 5 and not set(now) & set(seen)
        assert f"set {expected_set}" in " ".join(m.value for m in at.markdown)
        seen += now


def test_start_over_returns_to_the_questions():
    at = press(answer(fresh(), STUDY), "Find my music")
    at = press(at, "Start over")
    assert not at.exception and not titles(at)
    assert all(g.value is None for g in at.button_group)
