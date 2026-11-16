"""Web discovery tool: find a song outside the catalog via the Spotify Web API.

Spotify results are treated as untrusted candidates: a pick is only shown if it passes
`verify_candidate`. A FixtureClient replays recorded results for tests and offline runs.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


from .catalog import Song
from .env import load_env
from .links import _plain, clean_title, primary_artist
from .log import get_logger

log = get_logger("web")
load_env()

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "web_tracks.json"


class WebSearchError(RuntimeError):
    """Search unavailable or failed (no credentials, network, bad status)."""


@dataclass(frozen=True)
class Track:
    title: str
    artist: str
    url: str
    popularity: int = 0
    source: str = "spotify"


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


class SpotifyClient:
    """Client-credentials flow: no user login needed, search only."""
    name = "spotify"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None, timeout: float = 15.0):
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET", "")
        self.timeout = timeout
        self._token = ""
        self._expires = 0.0

    @property
    def available(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_token(self) -> str:
        if self._token and time.time() < self._expires - 30:
            return self._token
        basic = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        req = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=b"grant_type=client_credentials", method="POST",
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.load(resp)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise WebSearchError(f"Spotify auth failed: {type(exc).__name__}") from exc
        self._token = data["access_token"]
        self._expires = time.time() + int(data.get("expires_in", 3600))
        return self._token

    def search_tracks(self, query: str, limit: int = 10) -> list[Track]:
        if not self.available:
            raise WebSearchError("Spotify credentials are not set")
        url = "https://api.spotify.com/v1/search?" + urllib.parse.urlencode(
            {"q": query, "type": "track", "limit": limit})
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self._get_token()}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                items = json.load(resp)["tracks"]["items"]
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
            raise WebSearchError(f"Spotify search failed: {type(exc).__name__}") from exc
        return [
            Track(t["name"], ", ".join(a["name"] for a in t["artists"]),
                  t.get("external_urls", {}).get("spotify", ""), int(t.get("popularity", 0)))
            for t in items if t.get("name") and t.get("artists")
        ]


    def lookup(self, title: str, artist: str) -> "Track | None":
        """Confirm a specific song exists on Spotify; returns it or None."""
        for t in self.search_tracks(f"track:{title} artist:{artist}", limit=5):
            if _same_song(t, title, artist):
                return t
        return None


class MusicBrainzClient:
    """Free, no-account fallback. Search by tags, or look up a specific recording."""
    name = "musicbrainz"
    available = True
    _last_call = 0.0

    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def _query(self, lucene: str, limit: int) -> list["Track"]:
        wait = 1.1 - (time.time() - MusicBrainzClient._last_call)  # public API: max ~1 request/second
        if wait > 0:
            time.sleep(wait)
        url = "https://musicbrainz.org/ws/2/recording?" + urllib.parse.urlencode(
            {"query": lucene, "fmt": "json", "limit": limit})
        req = urllib.request.Request(url, headers={"User-Agent": "musicrag-student-project/0.1"})
        recs = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    recs = json.load(resp)["recordings"]
                break
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503) and attempt < 2:
                    log.warning("MusicBrainz busy (%s), retrying", exc.code)
                    time.sleep(3 * (attempt + 1))
                    continue
                raise WebSearchError(f"MusicBrainz search failed: HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
                raise WebSearchError(f"MusicBrainz search failed: {type(exc).__name__}") from exc
            finally:
                MusicBrainzClient._last_call = time.time()
        return [
            Track(r["title"], ", ".join(a["name"] for a in r.get("artist-credit", []) if "name" in a),
                  f"https://musicbrainz.org/recording/{r['id']}", int(r.get("score", 0)), "musicbrainz")
            for r in recs if r.get("title") and r.get("artist-credit")
        ]

    def search_tracks(self, query: str, limit: int = 10) -> list["Track"]:
        words = [w for w in query.lower().split() if w.isalpha() and len(w) > 2][:3]
        if not words:
            return []
        return self._query(" AND ".join(f'tag:"{w}"' for w in words), limit)

    def lookup(self, title: str, artist: str) -> "Track | None":
        esc = lambda x: x.replace('"', " ")  # noqa: E731
        for t in self._query(f'recording:"{esc(title)}" AND artist:"{esc(artist)}"', 5):
            if _same_song(t, title, artist) and t.popularity >= 90:
                return t
        return None


class FixtureClient:
    """Replays recorded tracks. Matches the first fixture key whose words all appear in the query."""
    name = "fixture"
    available = True

    def __init__(self, path: Path = FIXTURE_PATH):
        self.data = json.loads(Path(path).read_text(encoding="utf-8"))

    def search_tracks(self, query: str, limit: int = 10) -> list[Track]:
        words = set(_norm(query).split())
        for key, tracks in self.data.items():
            if set(key.split()) <= words:
                return [Track(**t, source="fixture") for t in tracks][:limit]
        return []

    def lookup(self, title: str, artist: str) -> "Track | None":
        for tracks in self.data.values():
            for t in tracks:
                tr = Track(**t, source="fixture")
                if _same_song(tr, title, artist):
                    return tr
        return None


def _same_song(track: "Track", title: str, artist: str) -> bool:
    """Same song if the cleaned titles match and the proposed lead artist is credited on the track.

    "Bangarang (feat. Sirah)" matches "Bangarang"; "DVBBS, Borgeous" matches "DVBBS & Borgeous".
    """
    return clean_title(track.title) == clean_title(title) and primary_artist(artist) in _plain(track.artist)


def verify_candidate(track: Track, catalog: list[Song], already: set) -> tuple[bool, str]:
    """Guardrail for web results. Returns (ok, reason)."""
    if not track.title.strip() or not track.artist.strip():
        return False, "missing title or artist"
    key = (_norm(track.title), _norm(track.artist))
    if key in already:
        return False, "already recommended"
    if any(_norm(s.title) == key[0] for s in catalog):
        return False, "title already in catalog"
    if track.source == "spotify" and not track.url.startswith("https://open.spotify.com/"):
        return False, "no valid Spotify link"
    return True, "ok"
