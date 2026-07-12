"""
Confidence scoring for company enrichment results.

This version uses:

1. Source Quality
2. LLM Completeness
3. Excel Agreement
4. LLM-as-a-Judge

Final Score = 100

This score represents how trustworthy the enrichment is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------
# Expected LLM Fields
# ---------------------------------------------------------

LLM_FIELDS: tuple[str, ...] = (
    "company_name",
    "industry",
    "description",
    "products",
    "services",
    "target_customers",
    "keywords",
    "website_summary",
)


# ---------------------------------------------------------
# Weight of every enrichment field
# ---------------------------------------------------------

FIELD_WEIGHTS: dict[str, float] = {
    "company_name": 1.0,
    "industry": 1.5,
    "description": 2.0,
    "products": 2.5,
    "services": 1.5,
    "target_customers": 1.0,
    "keywords": 1.0,
    "website_summary": 1.5,
}


# ---------------------------------------------------------
# Comparator penalties
# ---------------------------------------------------------

CHANGE_TYPE_PENALTIES = {
    "modified": 10,
    "missing_in_llm": 8,
    "added_in_llm": 2,
}


# ---------------------------------------------------------
# Final section weights
# ---------------------------------------------------------

MAX_SOURCE_SCORE = 20
MAX_COMPLETENESS_SCORE = 20
MAX_AGREEMENT_SCORE = 20
MAX_JUDGE_SCORE = 40


CONFIDENCE_LEVELS = (
    ("High", 85),
    ("Medium", 65),
    ("Low", 0),
)


# ---------------------------------------------------------
# Result Dataclass
# ---------------------------------------------------------

@dataclass
class ConfidenceScore:

    confidence_score: float

    confidence_level: str

    breakdown: dict[str, float] = field(default_factory=dict)

    factors: list[str] = field(default_factory=list)

    def to_dict(self):

        return {
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "breakdown": self.breakdown,
            "factors": self.factors,
        }


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def _is_empty(value: Any) -> bool:

    if value is None:
        return True

    if isinstance(value, str):
        return value.strip().lower() in {
            "",
            "nan",
            "none",
            "null",
        }

    if isinstance(value, (list, tuple, set)):
        return len(value) == 0

    return False


def _clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
):

    return max(minimum, min(maximum, value))


def _confidence_level(score: float) -> str:

    for level, threshold in CONFIDENCE_LEVELS:

        if score >= threshold:
            return level

    return "Low"


# ---------------------------------------------------------
# Source Quality
# ---------------------------------------------------------

def _score_source_quality(
    *,
    website_valid: bool,
    email_valid: bool,
    clean_text_length: int,
):

    score = 0.0

    reasons = []

    if website_valid:
        score += 8
        reasons.append("Website URL is valid (+8)")
    else:
        reasons.append("Invalid website URL")

    if email_valid:
        score += 4
        reasons.append("Email format valid (+4)")
    else:
        reasons.append("Email invalid")

    if clean_text_length >= 1000:
        score += 8
        reasons.append("Rich website content (+8)")

    elif clean_text_length >= 500:
        score += 6
        reasons.append("Good website content (+6)")

    elif clean_text_length >= 200:
        score += 4
        reasons.append("Limited website content (+4)")

    elif clean_text_length > 0:
        score += 2
        reasons.append("Very little content (+2)")

    else:
        reasons.append("No website content")

    return _clamp(score, 0, MAX_SOURCE_SCORE), reasons


# ---------------------------------------------------------
# LLM Completeness
# ---------------------------------------------------------

def _score_llm_completeness(llm_output: dict):

    earned = 0

    total = sum(FIELD_WEIGHTS.values())

    reasons = []

    for field_name in LLM_FIELDS:

        weight = FIELD_WEIGHTS[field_name]

        if not _is_empty(llm_output.get(field_name)):
            earned += weight
            reasons.append(f"{field_name} extracted")

        else:
            reasons.append(f"{field_name} missing")

    score = (earned / total) * MAX_COMPLETENESS_SCORE

    return _clamp(score, 0, MAX_COMPLETENESS_SCORE), reasons
    # ---------------------------------------------------------
# Excel vs LLM Agreement
# ---------------------------------------------------------

def _score_agreement(comparison: dict):

    score = MAX_AGREEMENT_SCORE

    reasons = []

    differences = comparison.get("differences", [])

    if not differences:
        reasons.append("Excel and LLM agree (+20)")
        return score, reasons

    for diff in differences:

        field = diff.get("field", "Unknown")

        change = diff.get("change_type", "modified")

        penalty = CHANGE_TYPE_PENALTIES.get(change, 8)

        score -= penalty

        if change == "modified":
            reasons.append(
                f"{field} modified by LLM (-{penalty})"
            )

        elif change == "missing_in_llm":
            reasons.append(
                f"{field} missing in LLM (-{penalty})"
            )

        elif change == "added_in_llm":
            reasons.append(
                f"{field} added by LLM (+enrichment)"
            )

        else:
            reasons.append(
                f"{field} mismatch (-{penalty})"
            )

    score = _clamp(score, 0, MAX_AGREEMENT_SCORE)

    return score, reasons


# ---------------------------------------------------------
# LLM-as-a-Judge Score
# ---------------------------------------------------------

def _score_llm_judge(judge_result: dict):

    """
    Uses llm_judge.py output.

    Example input

    {
        "judge_score":90,
        "decision":"PASS",
        "hallucination":False,
        "supported_fields":[...],
        "unsupported_fields":[...],
        "missing_information":[...]
    }
    """

    reasons = []

    raw_score = float(judge_result.get("judge_score", 0))

    score = (raw_score / 100) * MAX_JUDGE_SCORE

    # -------------------------
    # Hallucination penalty
    # -------------------------

    if judge_result.get("hallucination"):

        score -= 10

        reasons.append(
            "Judge detected hallucination (-10)"
        )

    else:

        reasons.append(
            "No hallucination detected"
        )

    # -------------------------
    # Supported fields
    # -------------------------

    supported = judge_result.get(
        "supported_fields",
        [],
    )

    if supported:

        reasons.append(
            f"{len(supported)} fields supported by website"
        )

    # -------------------------
    # Unsupported fields
    # -------------------------

    unsupported = judge_result.get(
        "unsupported_fields",
        [],
    )

    if unsupported:

        deduction = min(
            len(unsupported) * 2,
            10,
        )

        score -= deduction

        reasons.append(
            f"{len(unsupported)} unsupported fields (-{deduction})"
        )

    # -------------------------
    # Missing information
    # -------------------------

    missing = judge_result.get(
        "missing_information",
        [],
    )

    if missing:

        reasons.append(
            "Missing on website: "
            + ", ".join(missing)
        )

    decision = judge_result.get(
        "decision",
        "",
    )

    if decision.upper() == "PASS":

        reasons.append(
            "LLM Judge approved enrichment"
        )

    else:

        reasons.append(
            "LLM Judge recommends review"
        )

    score = _clamp(
        score,
        0,
        MAX_JUDGE_SCORE,
    )

    return score, reasons
    # ---------------------------------------------------------
# Main Function
# ---------------------------------------------------------

def calculate_confidence_score(
    *,
    comparison: dict[str, Any],
    llm_output: dict[str, Any],
    judge_result: dict[str, Any] | None = None,
    website_valid: bool = True,
    email_valid: bool = False,
    clean_text_length: int = 0,
) -> dict[str, Any]:
    """
    Calculate the overall confidence score.

    Components

    20 -> Source Quality
    20 -> LLM Completeness
    20 -> Excel Agreement
    40 -> LLM Judge

    Total = 100
    """

    # -------------------------------------------------
    # Source Quality
    # -------------------------------------------------

    source_score, source_reasons = _score_source_quality(
        website_valid=website_valid,
        email_valid=email_valid,
        clean_text_length=clean_text_length,
    )

    # -------------------------------------------------
    # LLM Completeness
    # -------------------------------------------------

    completeness_score, completeness_reasons = (
        _score_llm_completeness(
            llm_output
        )
    )

    # -------------------------------------------------
    # Comparator
    # -------------------------------------------------

    agreement_score, agreement_reasons = (
        _score_agreement(
            comparison
        )
    )

    # -------------------------------------------------
    # Judge
    # -------------------------------------------------

    if judge_result:

        judge_score, judge_reasons = (
            _score_llm_judge(
                judge_result
            )
        )

    else:

        judge_score = 0

        judge_reasons = [
            "LLM Judge not executed"
        ]

    # -------------------------------------------------
    # Final Score
    # -------------------------------------------------

    final_score = _clamp(

        source_score

        + completeness_score

        + agreement_score

        + judge_score,

        0,

        100,
    )

    confidence = ConfidenceScore(

        confidence_score=round(
            final_score,
            1,
        ),

        confidence_level=_confidence_level(
            final_score
        ),

        breakdown={

            "source_quality": round(
                source_score,
                1,
            ),

            "llm_completeness": round(
                completeness_score,
                1,
            ),

            "excel_agreement": round(
                agreement_score,
                1,
            ),

            "llm_judge": round(
                judge_score,
                1,
            ),

        },

        factors=(

            source_reasons

            + completeness_reasons

            + agreement_reasons

            + judge_reasons

        ),

    )

    logger.info(
        "Confidence Score = %.1f (%s)",
        confidence.confidence_score,
        confidence.confidence_level,
    )

    return confidence.to_dict()