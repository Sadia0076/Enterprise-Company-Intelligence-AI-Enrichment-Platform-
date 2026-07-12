"""
LLM client for company enrichment using the Groq API.

Calls Groq's OpenAI-compatible endpoint and returns structured JSON.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import APIError, APITimeoutError, OpenAI

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
ENV_FILE: Path = PROJECT_ROOT / ".env"

GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL: str = "llama-3.3-70b-versatile"
DEFAULT_TIMEOUT_SECONDS: float = 60.0
MAX_WEBSITE_TEXT_CHARS: int = 12_000

COMPANY_ANALYSIS_SCHEMA: dict[str, Any] = {
    "company_name": "string",
    "industry": "string",
    "description": "string",
    "products": ["string"],
    "services": ["string"],
    "target_customers": "string",
    "keywords": ["string"],
    "website_summary": "string",
}


class LLMClientError(Exception):
    """Raised when company analysis via Groq fails."""


def analyze_company(
    *,
    company_name: str,
    website_text: str,
    website: str = "",
) -> dict[str, Any]:
    """
    Analyze a company using scraped website text and return structured JSON.

    Args:
        company_name: Company name from input data.
        website_text: Cleaned text extracted from the company website.
        website: Optional company website URL.

    Returns:
        Dictionary with enrichment fields such as industry, products,
        services, description, and keywords.

    Raises:
        LLMClientError: Missing API key, API failure, or invalid JSON response.
    """
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE)

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise LLMClientError(
            "GROQ_API_KEY is not set. Add it to your environment or .env file."
        )

    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()
    timeout_seconds = float(
        os.getenv("GROQ_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    )

    company_name = company_name.strip()
    website = website.strip()
    website_text = website_text.strip()

    if not company_name:
        raise LLMClientError("company_name is required.")
    if not website_text:
        raise LLMClientError("website_text is required.")

    if len(website_text) > MAX_WEBSITE_TEXT_CHARS:
        website_text = website_text[:MAX_WEBSITE_TEXT_CHARS]
        logger.warning(
            "Truncated website_text to %d characters for %s",
            MAX_WEBSITE_TEXT_CHARS,
            company_name,
        )

    client = OpenAI(
        api_key=api_key,
        base_url=GROQ_BASE_URL,
        timeout=timeout_seconds,
    )

    system_prompt = (
        "You are a B2B company enrichment assistant. "
        "Analyze the provided website content and return ONLY valid JSON. "
        "Do not include markdown or explanations."
    )

    user_prompt = f"""
Company name: {company_name}
Website: {website or "unknown"}

Website content:
{website_text}

Return JSON with exactly these keys:
{json.dumps(COMPANY_ANALYSIS_SCHEMA, indent=2)}

Rules:
- Use only information supported by the website content.
- If a field is unknown, use an empty string or empty list.
- products and services must be arrays of strings.
- keywords must be 3 to 10 short terms.
""".strip()

    logger.info("Analyzing company with Groq: %s", company_name)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except APITimeoutError as exc:
        raise LLMClientError(f"Groq request timed out for {company_name}") from exc
    except APIError as exc:
        raise LLMClientError(f"Groq API error for {company_name}: {exc}") from exc
    except Exception as exc:
        raise LLMClientError(
            f"Unexpected Groq client error for {company_name}: {exc}"
        ) from exc

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise LLMClientError(f"Empty response from Groq for {company_name}")

    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise LLMClientError(
            f"Groq returned invalid JSON for {company_name}: {exc}"
        ) from exc

    if not isinstance(result, dict):
        raise LLMClientError(
            f"Groq response for {company_name} is not a JSON object"
        )

    logger.debug("Groq analysis completed for %s", company_name)
    return result