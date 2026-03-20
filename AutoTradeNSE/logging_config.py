"""
logging_config.py

Centralized logging setup for AutoTradeNSE. Call `setup_logging()` from
the application's entrypoint to enable console (and optional file) logging
at DEBUG level.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from typing import Optional


def setup_logging(level: int = logging.DEBUG, log_file: Optional[str] = None,
                  max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> logging.Logger:
    """Configure the root logger.

    - level: logging level, default DEBUG
    - log_file: optional path to a rotating log file
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to allow repeated calls (useful in tests)
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # Console handler
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)
    root.addHandler(sh)

    # Optional rotating file handler
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception:
                # Best-effort directory creation; if it fails, continue without file logging
                pass
        fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes,
                                                  backupCount=backup_count, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root.addHandler(fh)

    return root
