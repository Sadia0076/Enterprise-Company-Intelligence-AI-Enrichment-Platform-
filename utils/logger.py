"""
Centralized logging configuration for the enrichment pipeline.

Provides console and rotating file handlers with a consistent format.
Call ``setup_logging()`` once at application startup; use ``get_logger()``
in modules thereafter.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Final

LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_FILE: Final[str] = "enrichment.log"
MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT: Final[int] = 5

_initialized: bool = False


def _resolve_level(level: str | int) -> int:
    """Convert a log level name or integer to a logging level constant."""
    if isinstance(level, int):
        return level
    numeric = logging.getLevelNamesMapping().get(level.upper())
    if numeric is None:
        raise ValueError(f"Invalid log level: {level!r}")
    return numeric


def _build_console_handler(level: int) -> logging.Handler:
    """Create a stdout console handler."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def _build_file_handler(log_file: Path, level: int) -> logging.Handler:
    """Create a rotating file handler."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def setup_logging(
    log_level: str | int | None = None,
    logs_dir: Path | None = None,
    log_file_name: str = DEFAULT_LOG_FILE,
    *,
    console: bool = True,
    file_logging: bool = True,
) -> None:
    """
    Configure application-wide logging (idempotent).

    If ``log_level`` or ``logs_dir`` are omitted, values are read from
    ``config.settings.get_settings()``.

    Args:
        log_level: Root log level (e.g. ``"INFO"``, ``"DEBUG"``).
        logs_dir: Directory for log files.
        log_file_name: Log file name inside ``logs_dir``.
        console: Enable console output.
        file_logging: Enable rotating file output.
    """
    global _initialized

    if _initialized:
        return

    if log_level is None or logs_dir is None:
        from config.settings import get_settings

        settings = get_settings()
        if log_level is None:
            log_level = settings.log_level
        if logs_dir is None:
            logs_dir = settings.logs_dir

    level = _resolve_level(log_level)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup is called before the guard fires.
    root_logger.handlers.clear()

    if console:
        root_logger.addHandler(_build_console_handler(level))

    if file_logging:
        log_path = Path(logs_dir) / log_file_name
        root_logger.addHandler(_build_file_handler(log_path, level))

    # Reduce noise from verbose third-party libraries.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _initialized = True
    root_logger.debug(
        "Logging initialized (level=%s, console=%s, file=%s)",
        logging.getLevelName(level),
        console,
        file_logging,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Ensures ``setup_logging()`` has run at least once using defaults
    from settings when not yet initialized.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        Configured ``logging.Logger`` instance.
    """
    if not _initialized:
        setup_logging()
    return logging.getLogger(name)