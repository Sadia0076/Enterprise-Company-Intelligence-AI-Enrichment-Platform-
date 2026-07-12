"""
Email format validation for product enrichment input data.

Validates that a string is a well-formed email address.
"""

from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email: str | None) -> bool:
    """
    Return True if *email* is a non-empty, well-formed email address.

    Args:
        email: Email string to validate.

    Returns:
        True when the email is valid, otherwise False.
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()
    if not email:
        return False

    return EMAIL_PATTERN.fullmatch(email) is not None