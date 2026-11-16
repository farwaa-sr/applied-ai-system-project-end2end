"""RAG retrieval layer: TF-IDF search over taste-profile archetypes and the song catalog.

Pure Python on purpose: no API key, no model download, fully reproducible.
Two corpora are indexed: (1) archetype documents in data/profiles/, (2) the song catalog.
"""
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .catalog import Song
from .log import get_logger

log = get_logger("retriever")

PROFILES_DIR = Path(__file__).resolve().parents[2] / "data" / "profiles"
STOPWORDS = frozenset(
    "a an and are as at be but by for from has in is it its of on or that the their this to was with who wants want"
    .split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9&]+", text.lower()) if t not in STOPWORDS and len(t) > 1]


@dataclass(frozen=True)
class Archetype:
    """A taste-profile document: structured targets plus free-text description."""
    name: str
    genres: tuple
    moods: tuple
    energy: tuple
    valence: tuple
    acousticness: tuple
    search_terms: tuple
    text: str

    def midpoint(self, field_name: str) -> float:
        lo, hi = getattr(self, field_name)
        return (lo + hi) / 2


def _rng(value: str) -> tuple:
    lo, hi = (float(x) for x in value.split("-"))
    return lo, hi


def parse_archetype(path: Path) -> Archetype:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    name = lines[0].lstrip("# ").strip()
    meta = {}
    for line in lines[1:]:
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            if k.strip() in {"genres", "moods", "energy", "valence", "acousticness", "search_terms"}:
                meta[k.strip()] = v.strip()
    listed = lambda v: tuple(x.strip() for x in v.split(","))  # noqa: E731
    return Archetype(
        name=name,
        genres=listed(meta["genres"]),
        moods=listed(meta["moods"]),
        energy=_rng(meta["energy"]),
        valence=_rng(meta["valence"]),
        acousticness=_rng(meta["acousticness"]),
        search_terms=listed(meta["search_terms"]),
        text=raw,
    )


def load_archetypes(directory: Path = PROFILES_DIR) -> list[Archetype]:
    """Load every archetype document. Malformed files are logged and skipped."""
    found = []
    for path in sorted(Path(directory).glob("*.md")):
        try:
            found.append(parse_archetype(path))
        except (KeyError, ValueError, IndexError) as exc:
            log.warning("Skipping archetype %s: %s", path.name, exc)
    if not found:
        raise FileNotFoundError(f"No valid archetype documents in {directory}")
    log.info("Loaded %d archetype documents", len(found))
    return found


@dataclass
class Hit:
    doc: object
    score: float


@dataclass
class TfidfIndex:
    """Small TF-IDF + cosine-similarity index over (doc, text) pairs."""
    docs: list
    _vectors: list = field(default_factory=list, repr=False)
    _idf: dict = field(default_factory=dict, repr=False)

    @classmethod
    def build(cls, pairs: list) -> "TfidfIndex":
        docs = [d for d, _ in pairs]
        tokenized = [tokenize(t) for _, t in pairs]
        df = Counter(tok for toks in tokenized for tok in set(toks))
        n = len(docs)
        idf = {tok: math.log((1 + n) / (1 + c)) + 1.0 for tok, c in df.items()}
        index = cls(docs=docs, _idf=idf)
        index._vectors = [index._vectorize(toks) for toks in tokenized]
        return index

    def _vectorize(self, tokens: list) -> dict:
        counts = Counter(t for t in tokens if t in self._idf)
        vec = {t: (1 + math.log(c)) * self._idf[t] for t, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def search(self, query: str, k: int = 3) -> list[Hit]:
        q = self._vectorize(tokenize(query))
        if not q:
            return []
        hits = [
            Hit(doc, sum(w * vec.get(t, 0.0) for t, w in q.items()))
            for doc, vec in zip(self.docs, self._vectors)
        ]
        hits = [h for h in hits if h.score > 0]
        hits.sort(key=lambda h: -h.score)
        return hits[:k]


def _energy_word(x: float) -> str:
    return "low energy calm slow" if x < 0.4 else "steady groove" if x < 0.7 else "high energy fast loud"


def _acoustic_word(x: float) -> str:
    return "acoustic organic warm" if x > 0.65 else "electronic produced" if x < 0.3 else "blend"


def song_text(s: Song) -> str:
    return f"{s.genre} {s.genre} {s.mood} {s.mood} {_energy_word(s.energy)} {_acoustic_word(s.acousticness)}"


class Retriever:
    """Searches both knowledge sources and returns ranked hits."""

    def __init__(self, archetypes: list[Archetype], songs: list[Song]):
        self.archetypes = archetypes
        self.songs = songs
        self._arch_index = TfidfIndex.build([(a, a.text) for a in archetypes])
        self._song_index = TfidfIndex.build([(s, song_text(s)) for s in songs])

    def archetypes_for(self, query: str, k: int = 3) -> list[Hit]:
        hits = self._arch_index.search(query, k)
        log.info("Retrieved archetypes %s", [(h.doc.name, round(h.score, 3)) for h in hits])
        return hits

    def songs_for(self, query: str, k: int = 5) -> list[Hit]:
        return self._song_index.search(query, k)
