"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

Run from the project root with either:
    python -m src.main
    python src/main.py
"""

try:
    from .recommender import MAX_SCORE, load_songs, recommend_songs  # python -m src.main
except ImportError:
    from recommender import MAX_SCORE, load_songs, recommend_songs  # python src/main.py


# Taste profiles: target values for the features used in scoring
PROFILES = {
    # Distinct, realistic listeners
    "High-Energy Pop": {
        "genre": "pop", "mood": "happy",
        "energy": 0.85, "valence": 0.80, "acousticness": 0.15,
    },
    "Chill Lofi": {
        "genre": "lofi", "mood": "chill",
        "energy": 0.40, "valence": 0.60, "acousticness": 0.80,
    },
    "Deep Intense Rock": {
        "genre": "rock", "mood": "intense",
        "energy": 0.92, "valence": 0.45, "acousticness": 0.08,
    },
    # Adversarial / edge cases
    "Conflicting: high energy but sad": {
        "genre": "blues", "mood": "sad",
        "energy": 0.90, "valence": 0.20, "acousticness": 0.10,
    },
    "Genre not in catalog": {
        "genre": "k-pop", "mood": "happy",
        "energy": 0.80, "valence": 0.85, "acousticness": 0.15,
    },
    "Impossible: loud and fully acoustic": {
        "genre": "folk", "mood": "dreamy",
        "energy": 0.95, "valence": 0.50, "acousticness": 0.95,
    },
    "Neutral: everything in the middle": {
        "genre": "jazz", "mood": "relaxed",
        "energy": 0.50, "valence": 0.50, "acousticness": 0.50,
    },
}


def show(name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Print the top k recommendations for one profile."""
    print(f"\n{'#' * 60}\nProfile: {name}")
    print(f"  {user_prefs['genre']} / {user_prefs['mood']}, "
          f"energy {user_prefs['energy']:.2f}, valence {user_prefs['valence']:.2f}, "
          f"acousticness {user_prefs['acousticness']:.2f}")
    print("=" * 60)
    for rank, (song, score, explanation) in enumerate(recommend_songs(user_prefs, songs, k=k), start=1):
        print(f"{rank}. {song['title']} by {song['artist']}  [{song['genre']}, {song['mood']}]")
        print(f"   Score: {score:.2f} / {MAX_SCORE:g}  ({explanation})")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for name, prefs in PROFILES.items():
        show(name, prefs, songs)


if __name__ == "__main__":
    main()
