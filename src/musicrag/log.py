"""Logging setup shared by every pipeline stage."""
import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes to logs/musicrag.log and the console."""
    logger = logging.getLogger(f"musicrag.{name}")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        LOG_DIR.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(LOG_DIR / "musicrag.log", encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError:
        pass  # file logging is best-effort; console still works
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    return logger
