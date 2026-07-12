"""
Compare Excel company data against LLM enrichment output.

Returns structured differences field by field.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

LIST_FIELDS: frozenset[str] = frozenset(
    {"products", "services", "keywords"}
)

# Excel column name -> LLM JSON key
DEFAULT_FIELD_MAPPING: dict[str, str] = {
    "full_name": "company_name",
    "company_name": "company_name",
    "name": "company_name",
    "industry": "industry",
    "description": "description",
    "company_description": "description",
    "products": "products",
    "services": "services",
    "target_customers": "target_customers",
    "keywords": "keywords",
    "website_summary": "website_summary",
}

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


@dataclass
class FieldDifference:
    """Difference for a single mapped field."""

    field: str
    excel_column: str | None
    llm_key: str
    excel_value: Any
    llm_value: Any
    change_type: str


@dataclass
class ComparisonResult:
    """Structured comparison between Excel and LLM data."""

    has_differences: bool
    total_differences: int
    differences: list[FieldDifference] = field(default_factory=list)
    llm_only_fields: list[str] = field(default_factory=list)
    excel_only_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to a JSON-serializable dictionary."""
        return {
            "has_differences": self.has_differences,
            "total_differences": self.total_differences,
            "differences": [
                {
                    "field": item.field,
                    "excel_column": item.excel_column,
                    "llm_key": item.llm_key,
                    "excel_value": item.excel_value,
                    "llm_value": item.llm_value,
                    "change_type": item.change_type,
                }
                for item in self.differences
            ],
            "llm_only_fields": self.llm_only_fields,
            "excel_only_columns": self.excel_only_columns,
        }


def _is_empty(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, float) and pd.isna(value):
        return True

    if isinstance(value, str):
        cleaned = value.strip().lower()
        return cleaned in {"", "nan", "none", "null"}

    if isinstance(value, (list, tuple, set)):
        return len(value) == 0

    return False


def _normalize_text(value: Any) -> str:
    if _is_empty(value):
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _normalize_list(value: Any) -> list[str]:
    if _is_empty(value):
        return []

    if isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value if not _is_empty(item)]
    else:
        items = [
            part.strip()
            for part in re.split(r"[,;|\n]+", str(value))
            if part.strip()
        ]

    normalized = sorted({_normalize_text(item) for item in items if item})
    return normalized


def _normalize_value(field_name: str, value: Any) -> str | list[str]:
    if field_name in LIST_FIELDS:
        return _normalize_list(value)
    return _normalize_text(value)


def _values_equal(field_name: str, excel_value: Any, llm_value: Any) -> bool:
    return _normalize_value(field_name, excel_value) == _normalize_value(
        field_name, llm_value
    )


def _build_field_mapping(
    excel_row: dict[str, Any],
    field_mapping: dict[str, str] | None,
) -> dict[str, str]:
    mapping = dict(DEFAULT_FIELD_MAPPING)
    if field_mapping:
        mapping.update(field_mapping)

    # Auto-map Excel columns that match LLM field names directly.
    for column in excel_row:
        column_name = str(column).strip()
        if column_name in LLM_FIELDS and column_name not in mapping:
            mapping[column_name] = column_name

    return mapping


def compare_excel_vs_llm(
    excel_row: dict[str, Any] | pd.Series,
    llm_output: dict[str, Any],
    *,
    field_mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Compare one Excel row against LLM enrichment output.

    Args:
        excel_row: One company record from Excel.
        llm_output: Structured JSON returned by analyze_company().
        field_mapping: Optional extra Excel column -> LLM key mappings.

    Returns:
        Dictionary with differences and metadata.
    """
    if isinstance(excel_row, pd.Series):
        excel_data = excel_row.to_dict()
    else:
        excel_data = dict(excel_row)

    llm_data = dict(llm_output or {})
    mapping = _build_field_mapping(excel_data, field_mapping)

    differences: list[FieldDifference] = []
    compared_llm_fields: set[str] = set()
    used_excel_columns: set[str] = set()

    for excel_column, llm_key in mapping.items():
        if excel_column not in excel_data:
            continue

        used_excel_columns.add(excel_column)
        compared_llm_fields.add(llm_key)

        excel_value = excel_data.get(excel_column)
        llm_value = llm_data.get(llm_key)

        if _values_equal(llm_key, excel_value, llm_value):
            continue

        excel_empty = _is_empty(excel_value)
        llm_empty = _is_empty(llm_value)

        if excel_empty and not llm_empty:
            change_type = "added_in_llm"
        elif not excel_empty and llm_empty:
            change_type = "missing_in_llm"
        else:
            change_type = "modified"

        differences.append(
            FieldDifference(
                field=llm_key,
                excel_column=excel_column,
                llm_key=llm_key,
                excel_value=excel_value,
                llm_value=llm_value,
                change_type=change_type,
            )
        )

    llm_only_fields = [
        field_name
        for field_name in LLM_FIELDS
        if field_name not in compared_llm_fields and not _is_empty(llm_data.get(field_name))
    ]

    excel_only_columns = [
        str(column)
        for column, value in excel_data.items()
        if str(column) not in used_excel_columns and not _is_empty(value)
    ]

    result = ComparisonResult(
        has_differences=bool(differences),
        total_differences=len(differences),
        differences=differences,
        llm_only_fields=llm_only_fields,
        excel_only_columns=excel_only_columns,
    )

    logger.debug(
        "Comparison completed: %d differences, %d llm-only fields",
        result.total_differences,
        len(result.llm_only_fields),
    )

    return result.to_dict()