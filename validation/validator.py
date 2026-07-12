"""
URL format validation for product enrichment input data.

Validates that a string is a well-formed HTTP/HTTPS URL.
"""

from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})


def is_valid_url(url: str | None) -> bool:
    """
    Return True if *url* is a non-empty HTTP/HTTPS URL with a host.

    Args:
        url: URL string to validate.

    Returns:
        True when the URL is valid, otherwise False.
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    if not url:
        return False

    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ALLOWED_SCHEMES:
        return False

    if not parsed.netloc:
        return False

    return True