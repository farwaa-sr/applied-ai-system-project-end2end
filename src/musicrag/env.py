"""Load variables from the project's .env file.

Uses python-dotenv when it is installed; otherwise falls back to a tiny built-in parser so the
app still starts in an environment where `pip install -r requirements.txt` has not been run.
"""
import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def load_env(path: Path = ENV_PATH) -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(path)
        return
    except ImportError:
        pass
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
