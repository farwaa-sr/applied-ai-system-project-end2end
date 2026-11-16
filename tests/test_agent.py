import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicrag.agent import MusicAgent  # noqa: E402
from musicrag.catalog import load_catalog  # noqa: E402
from musicrag.llm import LLMError  # noqa: E402
from musicrag.questions import InvalidAnswers  # noqa: E402
from musicrag.retriever import Retriever, load_archetypes  # noqa: E402
from musicrag.web import FixtureClient, Track, WebSearchError, verify_candidate  # noqa: E402

STUDY = {"setting": "a", "energy": "a", "mood": "b", "texture": "a", "novelty": "b"}
GYM = {"setting": "b", "energy": "c", "mood": "d", "texture": "c", "novelty": "c"}
FAMILIAR = {**STUDY, "novelty": "a"}


class FakeLLM:
    available = True

    def __init__(self, responses=None, fail=False):
        self.responses, self.fail, self.calls = list(responses or []), fail, 0

    def generate_json(self, prompt, retries=1):
        self.calls += 1
        if self.fail:
            raise LLMError("boom")
        return self.responses.pop(0)


class BrokenWeb:
    name, available = "broken", True

    def search_tracks(self, q, limit=10):
        raise WebSearchError("down")

    def lookup(self, t, a):
        raise WebSearchError("down")


@pytest.fixture(scope="module")
def parts():
    songs = load_catalog()
    return Retriever(load_archetypes(), songs), songs


def make(parts, llm=None, web=None):
    r, songs = parts
    return MusicAgent(r, songs, llm=llm, web_clients=web or [], fallback_web=FixtureClient())


def test_offline_run_returns_five_picks(parts):
    res = make(parts).run(STUDY)
    assert len(res.picks) == 5
    assert res.picks[0].kind == "catalog" and res.profile.genre in {"lofi", "ambient"}


def test_rag_changes_the_profile(parts):
    agent = make(parts)
    with_rag, without = agent.run(STUDY), agent.run(STUDY, use_rag=False)
    assert with_rag.profile.source != without.profile.source
    assert with_rag.confidence > without.confidence


def test_familiar_novelty_skips_web(parts):
    res = make(parts).run(FAMILIAR)
    assert all(p.kind == "catalog" for p in res.picks)


def test_new_novelty_adds_two_verified_web_picks(parts):
    res = make(parts).run(GYM)
    web = [p for p in res.picks if p.kind == "web"]
    assert len(web) == 2 and len(res.picks) == 5
    catalog_titles = {s.title.lower() for s in parts[1]}
    assert all(p.title.lower() not in catalog_titles for p in web)


def test_llm_failure_falls_back_and_stops_calling(parts):
    llm = FakeLLM(fail=True)
    res = make(parts, llm=llm).run(STUDY)
    assert "llm_unavailable" in res.flags and len(res.picks) == 5
    assert llm.calls == 1  # circuit breaker: no repeated calls after the first failure


def test_invalid_llm_profile_values_are_rejected(parts):
    bad = {"genre": "made-up-genre", "mood": "???", "energy": "loud", "valence": 5,
           "acousticness": -2, "confidence": "high", "rationale": "x"}
    res = make(parts, llm=FakeLLM([bad, {}, {}])).run(FAMILIAR)
    p = res.profile
    assert p.genre in {s.genre for s in parts[1]} and 0 <= p.energy <= 1
    assert 0 <= p.valence <= 1 and 0 <= p.acousticness <= 1


def test_llm_hallucinated_song_is_not_recommended(parts):
    llm = FakeLLM([
        {"genre": "lofi", "mood": "chill", "energy": 0.3, "valence": 0.6, "acousticness": 0.8,
         "confidence": 0.9, "rationale": "ok"},
        {"candidates": [{"title": "Totally Invented Song", "artist": "Nobody At All"}]},
        {},
    ])
    res = make(parts, llm=llm, web=[FixtureClient()]).run(STUDY)
    assert "Totally Invented Song" not in [p.title for p in res.picks]


def test_web_outage_falls_back_to_fixtures(parts):
    res = make(parts, web=[BrokenWeb()]).run(STUDY)
    assert any(p.source == "fixture" for p in res.picks)
    assert "web_fallback_fixture" in res.flags


def test_invalid_answers_raise(parts):
    with pytest.raises(InvalidAnswers):
        make(parts).run({"setting": "z"})


def test_verify_rejects_catalog_duplicate_and_bad_tracks(parts):
    songs = parts[1]
    assert not verify_candidate(Track("Smells Like Teen Spirit", "X", "u", source="fixture"), songs, set())[0]
    assert not verify_candidate(Track("", "X", "u", source="fixture"), songs, set())[0]
    assert not verify_candidate(Track("New", "X", "http://evil.example", source="spotify"), songs, set())[0]
    assert verify_candidate(Track("New", "X", "https://open.spotify.com/track/1"), songs, set())[0]
