"""
Logging configuration (Day 13, Section 15: "Logging and monitoring:
track system failures and edge cases").

Replaces scattered print() statements with real logging -- writes to
both the console and a rotating log file, so failures survive after the
terminal window is gone. call setup_logging() once at app startup
(app/main.py does this).
"""

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("app")
    if logger.handlers:
        return logger  # already configured (e.g. --reload re-import)

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=2_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
