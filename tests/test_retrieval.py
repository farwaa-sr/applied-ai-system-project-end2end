import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicrag.catalog import load_catalog  # noqa: E402
from musicrag.questions import InvalidAnswers, build_query, normalize_answers  # noqa: E402
from musicrag.retriever import Retriever, load_archetypes  # noqa: E402

STUDY = {"setting": "a", "energy": "a", "mood": "b", "texture": "a", "novelty": "b"}
GYM = {"setting": "b", "energy": "c", "mood": "d", "texture": "c", "novelty": "a"}


@pytest.fixture(scope="module")
def retriever():
    return Retriever(load_archetypes(), load_catalog())


def test_valid_answers_normalize():
    assert normalize_answers({**STUDY, "mood": " B "})["mood"] == "b"


@pytest.mark.parametrize("bad", [{}, None, {"setting": "a"}, {**STUDY, "mood": "z"}])
def test_invalid_answers_rejected(bad):
    with pytest.raises(InvalidAnswers):
        normalize_answers(bad)


def test_all_archetypes_parse():
    arch = load_archetypes()
    assert len(arch) >= 8
    for a in arch:
        assert a.energy[0] < a.energy[1] and a.genres and a.search_terms


def test_study_answers_retrieve_study_archetype(retriever):
    hits = retriever.archetypes_for(build_query(normalize_answers(STUDY)), k=3)
    assert hits[0].doc.name.startswith("Late-night study")


def test_gym_answers_retrieve_high_energy_archetype(retriever):
    hits = retriever.archetypes_for(build_query(normalize_answers(GYM)), k=3)
    assert hits[0].doc.energy[0] >= 0.85


def test_empty_query_returns_nothing(retriever):
    assert retriever.archetypes_for("", k=3) == []


def test_song_retrieval_returns_catalog_songs(retriever):
    hits = retriever.songs_for("lofi chill low energy acoustic", k=3)
    assert hits and hits[0].doc.genre in {"lofi", "ambient"}
