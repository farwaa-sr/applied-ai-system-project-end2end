"""Taste-profile construction: a deterministic baseline from retrieved archetypes,
optionally refined by the LLM and then validated.

The LLM never has the last word: its output is checked against the catalog vocabulary
and numeric ranges, and anything invalid falls back to the baseline value.
"""
from dataclasses import asdict, dataclass

from .catalog import Song
from .llm import GeminiClient, LLMError
from .log import get_logger
from .questions import describe, option_for
from .retriever import Hit

log = get_logger("profile")

ANSWER_WEIGHT = 0.6  # how strongly the explicit answer beats the retrieved archetype


@dataclass(frozen=True)
class TasteProfile:
    genre: str
    mood: str
    energy: float
    valence: float
    acousticness: float
    confidence: float
    source: str       # "baseline" or "llm"
    rationale: str

    def as_dict(self) -> dict:
        return asdict(self)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _weighted(hits: list[Hit], field_name: str) -> float:
    total = sum(h.score for h in hits) or 1.0
    return sum(h.score * h.doc.midpoint(field_name) for h in hits) / total


def baseline_profile(answers: dict, hits: list[Hit], genres: set) -> TasteProfile:
    """Blend the explicit answers with the retrieved archetypes. Needs at least one hit."""
    if not hits:
        raise ValueError("baseline_profile needs at least one retrieved archetype")
    top = hits[0]
    energy = ANSWER_WEIGHT * option_for(answers, "energy").value + (1 - ANSWER_WEIGHT) * _weighted(hits, "energy")
    acoustic = (ANSWER_WEIGHT * option_for(answers, "texture").value
                + (1 - ANSWER_WEIGHT) * _weighted(hits, "acousticness"))
    valence = _weighted(hits, "valence")
    mood = option_for(answers, "mood").value
    genre = next((g for g in top.doc.genres if g in genres), top.doc.genres[0])
    agrees = mood in top.doc.moods
    confidence = min(1.0, 0.3 + top.score + (0.1 if agrees else 0.0))
    return TasteProfile(
        genre=genre, mood=mood,
        energy=round(_clamp(energy), 2), valence=round(_clamp(valence), 2),
        acousticness=round(_clamp(acoustic), 2), confidence=round(confidence, 2),
        source="baseline",
        rationale=(f"Closest archetype '{top.doc.name}' (similarity {top.score:.2f}); "
                   f"answers set energy/texture/mood"
                   f"{'; mood agrees with archetype' if agrees else ''}."),
    )


def answers_only_profile(answers: dict, songs: list[Song]) -> TasteProfile:
    """Ablation baseline with retrieval switched OFF: uses only the raw answers and the
    catalog's own songs for that mood. Used to show what RAG adds."""
    mood = option_for(answers, "mood").value
    same_mood = [s for s in songs if s.mood == mood] or songs
    genre = max({s.genre for s in same_mood}, key=lambda g: sum(s.genre == g for s in same_mood))
    return TasteProfile(
        genre=genre, mood=mood,
        energy=round(float(option_for(answers, "energy").value), 2),
        valence=round(sum(s.valence for s in same_mood) / len(same_mood), 2),
        acousticness=round(float(option_for(answers, "texture").value), 2),
        confidence=0.4, source="answers-only (no retrieval)",
        rationale="Retrieval disabled: genre and valence guessed from catalog songs sharing the mood.",
    )


def _prompt(answers: dict, hits: list[Hit], base: TasteProfile, genres: set, moods: set) -> str:
    docs = "\n\n".join(f"[{i + 1}] {h.doc.text.strip()}" for i, h in enumerate(hits))
    return (
        "You are the profile-building step of a music recommender.\n"
        f"Listener answers: {describe(answers)}\n\n"
        f"Retrieved taste archetypes (use ONLY these as evidence):\n{docs}\n\n"
        f"Draft profile from rules: {base.as_dict()}\n\n"
        "Refine the draft into the listener's taste profile. Return a JSON object with keys: "
        "genre (string), mood (string), energy, valence, acousticness (numbers 0-1), "
        "confidence (number 0-1, how well the evidence supports the profile), "
        "rationale (one sentence citing which archetype you relied on).\n"
        f"genre must be one of {sorted(genres)}; mood must be one of {sorted(moods)}."
    )


def refine_with_llm(llm: GeminiClient, answers: dict, hits: list[Hit], base: TasteProfile,
                    songs: list[Song]) -> TasteProfile:
    """Ask the LLM to refine the baseline. Invalid fields keep their baseline value.

    Raises LLMError if the call itself fails (the agent decides how to fall back).
    """
    genres, moods = {s.genre for s in songs}, {s.mood for s in songs}
    data = llm.generate_json(_prompt(answers, hits, base, genres, moods))
    fixes = []

    def pick(key, allowed, default):
        val = str(data.get(key, "")).strip().lower()
        if val in allowed:
            return val
        fixes.append(key)
        return default

    def num(key, default):
        try:
            return round(_clamp(float(data[key])), 2)
        except (KeyError, TypeError, ValueError):
            fixes.append(key)
            return default

    profile = TasteProfile(
        genre=pick("genre", genres, base.genre), mood=pick("mood", moods, base.mood),
        energy=num("energy", base.energy), valence=num("valence", base.valence),
        acousticness=num("acousticness", base.acousticness),
        confidence=num("confidence", base.confidence),
        source="llm",
        rationale=str(data.get("rationale", "")).strip()[:300] or base.rationale,
    )
    if fixes:
        log.warning("LLM profile had invalid fields %s; kept baseline values", fixes)
    return profile


__all__ = ["TasteProfile", "baseline_profile", "refine_with_llm", "LLMError"]
