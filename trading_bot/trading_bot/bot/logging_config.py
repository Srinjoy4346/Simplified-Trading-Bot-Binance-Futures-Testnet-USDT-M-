"""
Centralized logging configuration for the trading bot.

Logs go to both console (INFO+) and a rotating log file (DEBUG+),
so full request/response/error detail is captured on disk while the
console stays readable.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading_bot.log")


def setup_logging(name: str = "trading_bot") -> logging.Logger:
    """Create (or return) a configured logger.

    Idempotent: safe to call multiple times (e.g. once per CLI invocation)
    without duplicating log handlers/lines.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        # Already configured (e.g. imported twice) — don't add duplicate handlers.
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler: full detail, keeps last 5 files of 2MB each.
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler: only INFO+ so normal runs aren't noisy.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
