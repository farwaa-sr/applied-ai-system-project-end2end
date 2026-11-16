"""Playback links: map a song to a Spotify track id so the UI can embed a player.

Ids for the catalog and the recorded fixtures are cached in data/spotify_ids.json (built by
scripts/resolve_spotify_ids.py), so playback needs no API call at runtime. Songs found live on
Spotify carry their link; everything else falls back to a Spotify search link.
"""
import json
import re
import unicodedata
import urllib.parse
from functools import lru_cache
from pathlib import Path

IDS_PATH = Path(__file__).resolve().parents[2] / "data" / "spotify_ids.json"


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def clean_title(title: str) -> str:
    """Lower-case title without (feat. ...), [remaster], punctuation or accents."""
    return _plain(re.sub(r"[\(\[].*?[\)\]]", "", title))


def primary_artist(artist: str) -> str:
    """First credited artist: 'Mark Ronson ft. Bruno Mars' -> 'mark ronson'."""
    first = re.split(r"\s+(?:ft\.?|feat\.?|featuring|&|x)\s+|,", artist, maxsplit=1, flags=re.I)[0]
    return _plain(first)


def song_key(title: str, artist: str) -> str:
    return f"{clean_title(title)}|{primary_artist(artist)}"


@lru_cache(maxsize=1)
def load_ids(path: Path = IDS_PATH) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def spotify_id_from_url(url: str) -> str | None:
    m = re.match(r"https://open\.spotify\.com/(?:intl-[a-z]+/)?track/([A-Za-z0-9]+)", url or "")
    return m.group(1) if m else None


def spotify_track_id(title: str, artist: str, url: str = "") -> str | None:
    return spotify_id_from_url(url) or load_ids().get(song_key(title, artist))


def embed_url(track_id: str) -> str:
    return f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator"


def search_url(title: str, artist: str) -> str:
    return "https://open.spotify.com/search/" + urllib.parse.quote(f"{title} {artist}")
