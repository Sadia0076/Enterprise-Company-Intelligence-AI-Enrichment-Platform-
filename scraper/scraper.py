"""
HTTP scraper for product enrichment.

Fetches a web page and returns its HTML content.
"""

from __future__ import annotations

import requests

from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT_SECONDS: float = 30.0
DEFAULT_USER_AGENT: str = (
    "Mozilla/5.0 (compatible; MunafahAI-Enrichment/1.0; +https://munafah.ai)"
)


class ScraperError(Exception):
    """Base exception for scraper failures."""


class ScraperRequestError(ScraperError):
    """Raised when the HTTP request fails (network, timeout, etc.)."""


class ScraperHTTPError(ScraperError):
    """Raised when the server returns a non-success HTTP status."""


class Scraper:
    """
    Fetch HTML from a website URL.

    Example:
        scraper = Scraper()
        html = scraper.fetch("https://example.com")
    """

    def __init__(
        self,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        """
        Initialize the scraper.

        Args:
            timeout_seconds: HTTP request timeout in seconds.
            user_agent: User-Agent header sent with each request.
        """
        self._timeout_seconds = timeout_seconds
        self._headers = {"User-Agent": user_agent}

    def fetch(self, url: str) -> str:
        """
        Visit *url* and return the page HTML.

        Args:
            url: Full HTTP/HTTPS URL to fetch.

        Returns:
            HTML content as a string.

        Raises:
            ScraperRequestError: Network failure, timeout, or connection error.
            ScraperHTTPError: Server returned 4xx/5xx status.
            ScraperError: Other unexpected failures.
        """
        url = url.strip()
        logger.info("Fetching URL: %s", url)

        try:
            response = requests.get(
                url,
                headers=self._headers,
                timeout=self._timeout_seconds,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            logger.error("Request failed for %s: %s", url, exc)
            raise ScraperRequestError(f"Failed to fetch {url}: {exc}") from exc

        if not response.ok:
            logger.error(
                "HTTP %s for %s",
                response.status_code,
                url,
            )
            raise ScraperHTTPError(
                f"HTTP {response.status_code} for {url}"
            )

        response.encoding = response.encoding or "utf-8"
        html = response.text
        logger.debug("Fetched %d characters from %s", len(html), url)
        return html


def fetch_html(url: str) -> str:
    """
    Convenience function to fetch HTML from a URL.

    Args:
        url: Full HTTP/HTTPS URL to fetch.

    Returns:
        HTML content as a string.

    Raises:
        ScraperError: On fetch failure.
    """
    return Scraper().fetch(url)