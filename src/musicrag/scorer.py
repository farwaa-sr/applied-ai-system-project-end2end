"""Rule-based song scorer, ported from the Music Recommender Simulation starter project.

Weights and rules are unchanged from the original `score_song`; the only difference is
that it now takes a TasteProfile and a Song dataclass instead of two dicts.
"""
from .catalog import Song
from .profile import TasteProfile

W_ENERGY = 7.0
W_VALENCE = 2.5
W_ACOUSTIC = 1.0
W_MOOD = 2.0
W_GENRE = 0.5
MAX_SCORE = W_ENERGY + W_VALENCE + W_ACOUSTIC + W_MOOD + W_GENRE


def score_song(profile: TasteProfile, song: Song) -> tuple[float, list[str]]:
    score, reasons = 0.0, []
    for name, weight in (("energy", W_ENERGY), ("valence", W_VALENCE), ("acousticness", W_ACOUSTIC)):
        gap = abs(getattr(song, name) - getattr(profile, name))
        points = weight * (1 - gap)
        score += points
        reasons.append(f"{name} gap {gap:.2f} (+{points:.2f})")
    for name, bonus in (("mood", W_MOOD), ("genre", W_GENRE)):
        if getattr(song, name) == getattr(profile, name):
            score += bonus
            reasons.append(f"{name} match (+{bonus:.1f})")
    return score, reasons


def rank_songs(profile: TasteProfile, songs: list[Song], k: int = 5) -> list[tuple[Song, float, list[str]]]:
    """Best-first; ties go to the closer energy, then the lower id."""
    scored = [(s, *score_song(profile, s)) for s in songs]
    scored.sort(key=lambda t: (-t[1], abs(t[0].energy - profile.energy), t[0].id))
    return scored[:k]
