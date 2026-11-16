import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicrag.catalog import load_catalog  # noqa: E402

HEADER = "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"


def test_default_catalog_loads():
    songs = load_catalog()
    assert len(songs) > 0
    assert all(0 <= s.energy <= 1 for s in songs)


def test_bad_rows_are_skipped(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text(
        HEADER
        + "1,Good,A,pop,happy,0.5,100,0.5,0.5,0.5\n"
        + "2,BadEnergy,A,pop,happy,1.5,100,0.5,0.5,0.5\n"
        + "x,BadId,A,pop,happy,0.5,100,0.5,0.5,0.5\n",
        encoding="utf-8",
    )
    songs = load_catalog(p)
    assert [s.title for s in songs] == ["Good"]


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_catalog(tmp_path / "nope.csv")


def test_missing_columns_raises(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("id,title\n1,x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_catalog(p)
