"""Record verified web results into tests/fixtures/web_tracks.json.

Each (title, artist) below is looked up live on MusicBrainz and only saved if the lookup
confirms it exists, so the fixtures contain real tracks, never invented ones.
Usage: python scripts/record_fixtures.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicrag.web import FIXTURE_PATH, MusicBrainzClient, WebSearchError  # noqa: E402

CANDIDATES = {
    "lofi": [("Sunset Lover", "Petit Biscuit"), ("Resonance", "HOME")],
    "ambient": [("Weightless", "Marconi Union"), ("An Ending (Ascent)", "Brian Eno")],
    "pop": [("Levitating", "Dua Lipa"), ("Blinding Lights", "The Weeknd")],
    "indie": [("Electric Feel", "MGMT"), ("Float On", "Modest Mouse")],
    "edm": [("Titanium", "David Guetta"), ("Animals", "Martin Garrix")],
    "rock": [("Seven Nation Army", "The White Stripes"), ("Mr. Brightside", "The Killers")],
    "metal": [("Master of Puppets", "Metallica"), ("Du hast", "Rammstein")],
    "reggae": [("Three Little Birds", "Bob Marley"), ("Could You Be Loved", "Bob Marley")],
    "soul": [("Let's Stay Together", "Al Green"), ("A Change Is Gonna Come", "Sam Cooke")],
    "blues": [("The Thrill Is Gone", "B.B. King"), ("Pride and Joy", "Stevie Ray Vaughan")],
    "classical": [("Clair de lune", "Claude Debussy"), ("Gymnopédie No. 1", "Erik Satie")],
    "jazz": [("Take Five", "The Dave Brubeck Quartet"), ("So What", "Miles Davis")],
    "folk": [("Fast Car", "Tracy Chapman"), ("Skinny Love", "Bon Iver")],
    "country": [("Jolene", "Dolly Parton"), ("Take Me Home, Country Roads", "John Denver")],
    "synthwave": [("Nightcall", "Kavinsky"), ("A Real Hero", "College")],
    "hip hop": [("Lose Yourself", "Eminem"), ("HUMBLE.", "Kendrick Lamar")],
    "r&b": [("Adorn", "Miguel"), ("Earned It", "The Weeknd")],
}


def main() -> None:
    client = MusicBrainzClient()
    out = {}
    for key, songs in CANDIDATES.items():
        for title, artist in songs:
            try:
                track = client.lookup(title, artist)
            except WebSearchError as exc:
                print(f"FAIL {key}: {title} - {artist} ({exc})")
                continue
            print(f"{'OK  ' if track else 'MISS'} {key}: {title} - {artist}")
            if track:
                out.setdefault(key, []).append(
                    {"title": track.title, "artist": track.artist, "url": track.url, "popularity": track.popularity})
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {sum(len(v) for v in out.values())} verified tracks to {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
