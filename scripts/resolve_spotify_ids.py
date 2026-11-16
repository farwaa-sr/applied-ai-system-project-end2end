"""Build data/spotify_ids.json: a Spotify track id for each catalog song and recorded fixture.

Needs SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET in .env (and, currently, a Premium app owner).
A result is accepted only if its cleaned title matches and the primary artist appears in the credits,
so a wrong song is never cached. Songs that cannot be matched are listed and left out.
Usage: python scripts/resolve_spotify_ids.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicrag.catalog import load_catalog  # noqa: E402
from musicrag.links import IDS_PATH, _plain, clean_title, primary_artist, song_key, spotify_id_from_url  # noqa: E402
from musicrag.web import FIXTURE_PATH, SpotifyClient, WebSearchError  # noqa: E402


def find_id(client: SpotifyClient, title: str, artist: str) -> str | None:
    want_title, want_artist = clean_title(title), primary_artist(artist)
    queries = [f'track:"{title}" artist:"{want_artist}"', f"{title} {want_artist}"]
    for q in queries:
        for t in client.search_tracks(q, limit=10):
            got = clean_title(t.title)
            if (got == want_title or got.startswith(want_title)) and want_artist in _plain(t.artist):
                return spotify_id_from_url(t.url)
    return None


def main() -> None:
    client = SpotifyClient()
    if not client.available:
        sys.exit("Spotify credentials are not set in .env")
    pairs = [(s.title, s.artist) for s in load_catalog()]
    fixtures = json.loads(Path(FIXTURE_PATH).read_text(encoding="utf-8"))
    pairs += [(t["title"], t["artist"]) for tracks in fixtures.values() for t in tracks]

    ids, missed = {}, []
    for title, artist in pairs:
        try:
            tid = find_id(client, title, artist)
        except WebSearchError as exc:
            print(f"FAIL {title} - {artist}: {exc}")
            missed.append((title, artist))
            continue
        print(f"{'OK  ' if tid else 'MISS'} {title} - {artist}")
        if tid:
            ids[song_key(title, artist)] = tid
        else:
            missed.append((title, artist))
    IDS_PATH.write_text(json.dumps(dict(sorted(ids.items())), indent=2), encoding="utf-8")
    print(f"\nWrote {len(ids)} ids to {IDS_PATH.name}; {len(missed)} unmatched: {missed}")


if __name__ == "__main__":
    main()
