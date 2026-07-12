"""
Application configuration loaded from environment variables.

Loads a `.env` file from the project root when present. Secrets such as API
keys must be supplied via environment variables — never hard-coded.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

logger = logging.getLogger(__name__)

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
ENV_FILE: Path = PROJECT_ROOT / ".env"


def _load_dotenv() -> None:
    """Load environment variables from `.env` if the file exists."""
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE)
        logger.debug("Loaded environment from %s", ENV_FILE)
    else:
        logger.debug(
            "No .env file found at %s; using process environment only",
            ENV_FILE,
        )


class Settings(BaseModel):
    """
    Central application settings.

    All values are sourced from environment variables. Use ``get_settings()``
    to obtain a cached singleton instance.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    # ------------------------------------------------------------------
    # Groq Configuration
    # ------------------------------------------------------------------

    groq_api_key: SecretStr = Field(
        ...,
        description="Groq API Key (env: GROQ_API_KEY)",
    )

    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Default Groq model (env: GROQ_MODEL)",
    )

    groq_timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        description="Groq timeout in seconds (env: GROQ_TIMEOUT_SECONDS)",
    )

    # ------------------------------------------------------------------
    # Scraper
    # ------------------------------------------------------------------

    scraper_request_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        description="HTTP request timeout (env: SCRAPER_REQUEST_TIMEOUT_SECONDS)",
    )

    scraper_user_agent: str = Field(
        default=(
            "Mozilla/5.0 (compatible; MunafahAI-Enrichment/1.0; "
            "+https://munafah.ai)"
        ),
        description="User-Agent for HTTP scraping (env: SCRAPER_USER_AGENT)",
    )

    playwright_headless: bool = Field(
        default=True,
        description="Run Playwright in headless mode (env: PLAYWRIGHT_HEADLESS)",
    )

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    data_dir: Path = Field(
        default=PROJECT_ROOT / "data",
        description="Input/output data directory (env: DATA_DIR)",
    )

    reports_dir: Path = Field(
        default=PROJECT_ROOT / "reports",
        description="Validation report output directory (env: REPORTS_DIR)",
    )

    logs_dir: Path = Field(
        default=PROJECT_ROOT / "logs",
        description="Log file directory (env: LOGS_DIR)",
    )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    log_level: str = Field(
        default="INFO",
        description="Root log level (env: LOG_LEVEL)",
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

        if normalized not in valid:
            raise ValueError(
                f"log_level must be one of {sorted(valid)}; got {value!r}"
            )

        return normalized

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables."""

        _load_dotenv()

        def _get_bool(name: str, default: bool) -> bool:
            raw = os.getenv(name)
            if raw is None:
                return default
            return raw.strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }

        def _get_float(name: str, default: float) -> float:
            raw = os.getenv(name)
            return float(raw) if raw is not None else default

        def _get_path(name: str, default: Path) -> Path:
            raw = os.getenv(name)
            return Path(raw) if raw else default

        return cls(
            groq_api_key=SecretStr(os.getenv("GROQ_API_KEY", "")),
            groq_model=os.getenv(
                "GROQ_MODEL",
                "llama-3.3-70b-versatile",
            ),
            groq_timeout_seconds=_get_float(
                "GROQ_TIMEOUT_SECONDS",
                60.0,
            ),
            scraper_request_timeout_seconds=_get_float(
                "SCRAPER_REQUEST_TIMEOUT_SECONDS",
                30.0,
            ),
            scraper_user_agent=os.getenv(
                "SCRAPER_USER_AGENT",
                (
                    "Mozilla/5.0 (compatible; MunafahAI-Enrichment/1.0; "
                    "+https://munafah.ai)"
                ),
            ),
            playwright_headless=_get_bool(
                "PLAYWRIGHT_HEADLESS",
                True,
            ),
            data_dir=_get_path(
                "DATA_DIR",
                PROJECT_ROOT / "data",
            ),
            reports_dir=_get_path(
                "REPORTS_DIR",
                PROJECT_ROOT / "reports",
            ),
            logs_dir=_get_path(
                "LOGS_DIR",
                PROJECT_ROOT / "logs",
            ),
            log_level=os.getenv(
                "LOG_LEVEL",
                "INFO",
            ),
        )

    def ensure_directories(self) -> None:
        """Create configured directories if they do not exist."""

        for directory in (
            self.data_dir,
            self.reports_dir,
            self.logs_dir,
        ):
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """

    settings = Settings.from_env()
    settings.ensure_directories()
    return settings