"""Launcher so the CLI runs from the project root in any shell, with no PYTHONPATH setup.

    python run.py                          interactive
    python run.py --answers a,a,b,a,b      non-interactive
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from musicrag.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
