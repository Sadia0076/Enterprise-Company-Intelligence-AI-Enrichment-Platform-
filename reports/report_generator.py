"""
Generate Validation.xlsx for the Company Enrichment Pipeline.

Creates ONE professional sheet that contains:

- Original Excel information
- Validation status
- LLM Enrichment
- LLM Judge results
- Confidence Score
- Human-readable recommendations

This report is designed for business users.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports"

DEFAULT_FILENAME = "Validation.xlsx"


class ReportGeneratorError(Exception):
    """Raised when report generation fails."""


def _format_value(value: Any) -> str:
    """Convert lists and None into readable strings."""

    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value)

    return str(value)


def _recommendation(record: dict[str, Any]) -> str:
    """
    Create a business-friendly recommendation.
    """

    judge = record.get("judge", {})

    recommendations = []

    if judge.get("missing_information"):

        recommendations.append(
            "Website does not mention: "
            + ", ".join(judge["missing_information"])
        )

    if judge.get("unsupported_fields"):

        recommendations.append(
            "LLM generated information that could not be verified: "
            + ", ".join(judge["unsupported_fields"])
        )

    if record.get("comparison", {}).get("differences"):

        recommendations.append(
            "Some Excel values differ from the website enrichment."
        )

    if not recommendations:

        recommendations.append(
            "Website contains sufficient information. No major issues detected."
        )

    return " | ".join(recommendations)


def _build_report_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Build ONE row per company containing:
    - Original Excel data
    - Validation results
    - LLM enrichment
    - LLM Judge
    - Confidence
    - Human recommendation
    """

    rows = []

    for record in records:

        comparison = record.get("comparison", {}) or {}
        confidence = record.get("confidence", {}) or {}
        judge = record.get("judge", {}) or {}
        llm = record.get("llm_output", {}) or {}
        original = record.get("excel_data", {}) or {}

        row = {}

        # -------------------------------------------------
        # ORIGINAL EXCEL DATA
        # -------------------------------------------------

        for column, value in original.items():
            row[column] = _format_value(value)

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        row["status"] = record.get("status", "")

        row["error_message"] = record.get("error_message", "")

        row["website_valid"] = record.get("website_valid", False)

        row["email_valid"] = record.get("email_valid", False)

        row["clean_text_length"] = record.get(
            "clean_text_length",
            0,
        )

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        row["confidence_score"] = confidence.get(
            "confidence_score",
            "",
        )

        row["confidence_level"] = confidence.get(
            "confidence_level",
            "",
        )

        breakdown = confidence.get("breakdown", {})

        row["source_quality_score"] = breakdown.get(
            "source_quality",
            "",
        )

        row["llm_completeness_score"] = breakdown.get(
            "llm_completeness",
            "",
        )

        row["agreement_score"] = breakdown.get(
            "data_agreement",
            "",
        )

        # -------------------------------------------------
        # LLM JUDGE
        # -------------------------------------------------

        row["judge_score"] = judge.get(
            "judge_score",
            "",
        )

        row["judge_decision"] = judge.get(
            "decision",
            "",
        )

        row["hallucination"] = judge.get(
            "hallucination",
            "",
        )

        row["supported_fields"] = _format_value(
            judge.get("supported_fields")
        )

        row["unsupported_fields"] = _format_value(
            judge.get("unsupported_fields")
        )

        row["missing_information"] = _format_value(
            judge.get("missing_information")
        )

        row["judge_reasoning"] = judge.get(
            "reasoning",
            "",
        )

        # -------------------------------------------------
        # COMPARATOR
        # -------------------------------------------------

        row["has_differences"] = comparison.get(
            "has_differences",
            False,
        )

        row["total_differences"] = comparison.get(
            "total_differences",
            0,
        )

        row["llm_only_fields"] = _format_value(
            comparison.get("llm_only_fields")
        )

        row["excel_only_columns"] = _format_value(
            comparison.get("excel_only_columns")
        )

        # -------------------------------------------------
        # LLM ENRICHMENT
        # -------------------------------------------------

        row["industry"] = _format_value(
            llm.get("industry")
        )

        row["description"] = _format_value(
            llm.get("description")
        )

        row["products"] = _format_value(
            llm.get("products")
        )

        row["services"] = _format_value(
            llm.get("services")
        )

        row["target_customers"] = _format_value(
            llm.get("target_customers")
        )

        row["keywords"] = _format_value(
            llm.get("keywords")
        )

        row["website_summary"] = _format_value(
            llm.get("website_summary")
        )

        # -------------------------------------------------
        # BUSINESS RECOMMENDATION
        # -------------------------------------------------

        row["recommendation"] = _recommendation(record)

        rows.append(row)

    return rows


def generate_validation_report(
    records: list[dict[str, Any]],
    *,
    output_dir: str | Path | None = None,
    filename: str = DEFAULT_FILENAME,
) -> Path:
    """
    Generate a single-sheet Validation Report.

    Each row contains:
    - Original Excel data
    - Validation results
    - LLM enrichment
    - Comparator results
    - LLM Judge results
    - Confidence score
    - Business recommendation
    """

    if not records:
        raise ReportGeneratorError(
            "No records provided for validation report."
        )

    reports_dir = (
        Path(output_dir)
        if output_dir
        else DEFAULT_REPORTS_DIR
    )

    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = reports_dir / filename

    report_df = pd.DataFrame(
        _build_report_rows(records)
    )

    try:

        with pd.ExcelWriter(
            output_path,
            engine="openpyxl",
        ) as writer:

            report_df.to_excel(
                writer,
                sheet_name="Validation_Report",
                index=False,
            )

            worksheet = writer.sheets["Validation_Report"]

            # Auto-fit columns
            for column_cells in worksheet.columns:

                length = max(
                    len(str(cell.value))
                    if cell.value is not None
                    else 0
                    for cell in column_cells
                )

                worksheet.column_dimensions[
                    column_cells[0].column_letter
                ].width = min(length + 3, 60)

    except Exception as exc:

        logger.exception(
            "Failed to generate report: %s",
            output_path,
        )

        raise ReportGeneratorError(
            f"Failed to generate report: {output_path}"
        ) from exc

    logger.info(
        "Validation report generated successfully: %s (%d companies)",
        output_path,
        len(records),
    )

    return output_path