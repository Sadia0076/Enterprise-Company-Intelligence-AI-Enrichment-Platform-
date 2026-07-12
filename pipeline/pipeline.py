"""
Main enrichment pipeline.

This module orchestrates the complete company enrichment workflow by
calling existing modules only.

Workflow:

Excel
    ↓
Validation
    ↓
Website Scraping
    ↓
HTML Parsing
    ↓
LLM Enrichment
    ↓
Comparator
    ↓
LLM Judge
    ↓
Confidence Scoring
    ↓
Validation Report
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from data.excel_reader import read_excel

from validation.validator import is_valid_url
from validation.email_validator import is_valid_email

from scraper.scraper import fetch_html
from scraper.parser import parse_html

from enrichment.llm_client import analyze_company
from enrichment.comparator import compare_excel_vs_llm
from enrichment.llm_judge import judge_enrichment
from enrichment.scoring import calculate_confidence_score

from reports.report_generator import generate_validation_report

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """
    Final pipeline result.
    """

    report_path: Path
    total_companies: int
    successful: int
    failed: int


def process_company(
    company: dict[str, Any],
) -> dict[str, Any]:
    """
    Process ONE company.

    This function does not contain business logic.
    It only calls the existing project modules in order.
    """

    company_name = str(company.get("full_name", "")).strip()
    website = str(company.get("website", "")).strip()
    email = str(company.get("e-mail", "")).strip()

    logger.info("=" * 60)
    logger.info("Processing company: %s", company_name)
    logger.info("=" * 60)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    website_valid = is_valid_url(website)
    email_valid = is_valid_email(email)

    # ---------------------------------------------------------
    # Website Scraping
    # ---------------------------------------------------------

    html = fetch_html(website)

    # ---------------------------------------------------------
    # HTML Parsing
    # ---------------------------------------------------------

    page = parse_html(
        html,
        base_url=website,
    )

    clean_text = page.clean_text

    logger.info(
        "Website parsed successfully (%d characters)",
        len(clean_text),
    )

    # ---------------------------------------------------------
    # LLM Enrichment
    # ---------------------------------------------------------

    llm_output = analyze_company(
        company_name=company_name,
        website=website,
        website_text=clean_text,
    )

    logger.info("LLM enrichment completed")

    # ---------------------------------------------------------
    # Compare Excel vs LLM
    # ---------------------------------------------------------

    comparison = compare_excel_vs_llm(
        excel_row=company,
        llm_output=llm_output,
    )

    logger.info(
        "Comparison completed (%d differences)",
        comparison.get("total_differences", 0),
    )

    # ---------------------------------------------------------
    # LLM Judge
    # ---------------------------------------------------------

    judge = judge_enrichment(
        website_text=clean_text,
        llm_output=llm_output,
        excel_data=company,
    )

    logger.info(
        "LLM Judge completed (Score: %s)",
        judge.get("judge_score"),
    )

    # ---------------------------------------------------------
    # Confidence Score
    # ---------------------------------------------------------

    confidence = calculate_confidence_score(
        comparison=comparison,
        llm_output=llm_output,
        judge_result=judge,
        website_valid=website_valid,
        email_valid=email_valid,
        clean_text_length=len(clean_text),
    )

    logger.info(
        "Confidence Score: %.1f",
        confidence["confidence_score"],
    )

    # ---------------------------------------------------------
    # Build Final Record
    # ---------------------------------------------------------

    record = {
        "company_name": company_name,
        "website": website,
        "email": email,
        "status": "success",
        "error_message": "",

        "website_valid": website_valid,
        "email_valid": email_valid,
        "clean_text_length": len(clean_text),

        "llm_output": llm_output,
        "comparison": comparison,
        "judge": judge,
        "confidence": confidence,
    }

    logger.info("Finished processing %s", company_name)

    return record


def run_pipeline(
    excel_file: str | Path,
) -> PipelineResult:
    """
    Run the complete enrichment pipeline.

    Steps
    -----
    1. Read Excel
    2. Process every company
    3. Generate Validation Report
    4. Return pipeline summary
    """

    excel_file = Path(excel_file)

    logger.info("=" * 70)
    logger.info("STARTING COMPANY ENRICHMENT PIPELINE")
    logger.info("=" * 70)

    # ---------------------------------------------------------
    # Read Excel
    # ---------------------------------------------------------

    dataframe = read_excel(excel_file)

    if dataframe.empty:
        raise ValueError("Excel file is empty.")

    logger.info(
        "Loaded %d companies",
        len(dataframe),
    )

    records: list[dict[str, Any]] = []

    successful = 0
    failed = 0

    # ---------------------------------------------------------
    # Process every company
    # ---------------------------------------------------------

    for index, row in dataframe.iterrows():

        logger.info(
            "Processing %d of %d",
            index + 1,
            len(dataframe),
        )

        try:

            record = process_company(
                row.to_dict(),
            )

            records.append(record)

            successful += 1

        except Exception as exc:

            logger.exception(
                "Failed processing company: %s",
                exc,
            )

            failed += 1

            company = row.to_dict()

            records.append(
                {
                    "company_name": company.get("full_name", ""),
                    "website": company.get("website", ""),
                    "email": company.get("e-mail", ""),
                    "status": "failed",
                    "error_message": str(exc),
                    "website_valid": False,
                    "email_valid": False,
                    "clean_text_length": 0,
                    "llm_output": {},
                    "comparison": {},
                    "judge": {},
                    "confidence": {},
                }
            )

    logger.info(
        "Pipeline Processing Finished"
    )

    # ---------------------------------------------------------
    # Generate Validation Report
    # ---------------------------------------------------------

    logger.info("Generating validation report...")

    report_path = generate_validation_report(
        records=records,
    )

    logger.info("Validation report saved to: %s", report_path)

    # ---------------------------------------------------------
    # Pipeline Summary
    # ---------------------------------------------------------

    logger.info("=" * 70)
    logger.info("PIPELINE COMPLETED")
    logger.info("=" * 70)
    logger.info("Total Companies : %d", len(dataframe))
    logger.info("Successful      : %d", successful)
    logger.info("Failed          : %d", failed)
    logger.info("Report          : %s", report_path)
    logger.info("=" * 70)

    return PipelineResult(
        report_path=report_path,
        total_companies=len(dataframe),
        successful=successful,
        failed=failed,
    )