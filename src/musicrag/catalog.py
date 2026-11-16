"""Data layer: load and validate the song catalog."""
import csv
from dataclasses import dataclass
from pathlib import Path

from .log import get_logger

log = get_logger("catalog")

DEFAULT_CSV = Path(__file__).resolve().parents[2] / "data" / "songs.csv"
FLOAT_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")
UNIT_FIELDS = ("energy", "valence", "danceability", "acousticness")
REQUIRED = ("id", "title", "artist", "genre", "mood") + FLOAT_FIELDS


@dataclass(frozen=True)
class Song:
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


def load_catalog(csv_path: Path = DEFAULT_CSV) -> list[Song]:
    """Load songs from CSV. Malformed rows are logged and skipped, not fatal."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Song catalog not found: {path}")

    songs: list[Song] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Catalog is missing columns: {missing}")
        for line_no, row in enumerate(reader, start=2):
            try:
                song = Song(
                    id=int(row["id"]),
                    title=row["title"].strip(),
                    artist=row["artist"].strip(),
                    genre=row["genre"].strip().lower(),
                    mood=row["mood"].strip().lower(),
                    **{k: float(row[k]) for k in FLOAT_FIELDS},
                )
                bad = [k for k in UNIT_FIELDS if not 0.0 <= getattr(song, k) <= 1.0]
                if bad or not song.title:
                    raise ValueError(f"invalid values: {bad or 'empty title'}")
                songs.append(song)
            except (ValueError, KeyError, TypeError) as exc:
                log.warning("Skipping row %d: %s", line_no, exc)

    log.info("Loaded %d songs from %s", len(songs), path.name)
    return songs
