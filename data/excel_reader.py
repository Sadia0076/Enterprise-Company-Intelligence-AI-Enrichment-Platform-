"""
Excel file reader for company enrichment input data.

Reads ``.xlsx`` / ``.xls`` files and returns a pandas DataFrame.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".xlsx", ".xls", ".xlsm"})


class ExcelReadError(Exception):
    """Base exception for Excel read failures."""


class ExcelFileNotFoundError(ExcelReadError):
    """Raised when the input file does not exist."""


class ExcelInvalidFormatError(ExcelReadError):
    """Raised when the file is not a supported Excel format."""


class ExcelEmptyError(ExcelReadError):
    """Raised when the workbook or selected sheet has no data."""


class ExcelReader:
    """
    Read company data from Excel files into a pandas DataFrame.

    Example:
        reader = ExcelReader()
        df = reader.read("data/companies.xlsx")
    """

    def __init__(self, engine: str = "openpyxl") -> None:
        """
        Initialize the reader.

        Args:
            engine: pandas Excel engine (default: ``openpyxl`` for ``.xlsx``).
        """
        self._engine = engine

    def read(
        self,
        file_path: str | Path,
        *,
        sheet_name: str | int = 0,
        **read_kwargs: Any,
    ) -> pd.DataFrame:
        """
        Read an Excel file and return its contents as a DataFrame.

        Args:
            file_path: Path to the Excel file.
            sheet_name: Sheet name or zero-based index (default: first sheet).
            **read_kwargs: Additional arguments passed to ``pandas.read_excel``.

        Returns:
            DataFrame with string column names stripped of leading/trailing
            whitespace.

        Raises:
            ExcelFileNotFoundError: File path does not exist.
            ExcelInvalidFormatError: Unsupported extension or corrupt workbook.
            ExcelEmptyError: Workbook or sheet contains no rows.
            ExcelReadError: Other read failures.
        """
        path = Path(file_path)
        self._validate_path(path)

        logger.info("Reading Excel file: %s (sheet=%r)", path, sheet_name)

        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet_name,
                engine=self._engine,
                **read_kwargs,
            )
        except FileNotFoundError as exc:
            logger.error("Excel file not found: %s", path)
            raise ExcelFileNotFoundError(f"File not found: {path}") from exc
        except ValueError as exc:
            logger.error("Invalid Excel content in %s: %s", path, exc)
            raise ExcelInvalidFormatError(
                f"Invalid or unreadable Excel file: {path}"
            ) from exc
        except ImportError as exc:
            logger.error("Missing Excel engine %r: %s", self._engine, exc)
            raise ExcelReadError(
                f"Excel engine {self._engine!r} is not available. "
                "Install openpyxl for .xlsx files."
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error reading Excel file: %s", path)
            raise ExcelReadError(f"Failed to read Excel file: {path}") from exc

        return self._post_process(df, path)

    def _validate_path(self, path: Path) -> None:
        """Validate that the path exists and has a supported extension."""
        if not path.exists():
            logger.error("Excel file not found: %s", path)
            raise ExcelFileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            logger.error("Path is not a file: %s", path)
            raise ExcelInvalidFormatError(f"Not a file: {path}")

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.error("Unsupported file extension: %s", path.suffix)
            raise ExcelInvalidFormatError(
                f"Unsupported extension {path.suffix!r}. "
                f"Expected one of: {sorted(SUPPORTED_EXTENSIONS)}"
            )

    def _post_process(self, df: pd.DataFrame, path: Path) -> pd.DataFrame:
        """Normalize column names and reject empty results."""
        if df is None or df.empty:
            logger.warning("Excel file contains no data: %s", path)
            raise ExcelEmptyError(f"Excel file is empty: {path}")

        # Normalize column headers for downstream modules.
        df = df.copy()
        df.columns = [str(col).strip() for col in df.columns]

        logger.info(
            "Successfully read %d rows and %d columns from %s",
            len(df),
            len(df.columns),
            path.name,
        )
        return df


def read_excel(
    file_path: str | Path,
    *,
    sheet_name: str | int = 0,
    **read_kwargs: Any,
) -> pd.DataFrame:
    """
    Convenience function to read an Excel file.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Sheet name or zero-based index.
        **read_kwargs: Additional arguments for ``pandas.read_excel``.

    Returns:
        Parsed DataFrame.

    Raises:
        ExcelReadError: On read failure.
    """
    return ExcelReader().read(file_path, sheet_name=sheet_name, **read_kwargs)