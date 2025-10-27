"""
Excel file parser supporting both .xlsx and .xls formats.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import FileParser, ParseResult


class ExcelParser(FileParser):
    """
    Parser for Excel files (.xlsx and .xls).
    Supports multiple sheets and various Excel formats.
    """

    SUPPORTED_EXTENSIONS = ['.xlsx', '.xls', '.xlsm']

    def validate(self, file_path: Path) -> bool:
        """Validate if file is Excel format."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    async def parse(
        self,
        file_path: Path,
        sheet_name: Optional[str] = None,
        skip_rows: int = 0,
        header_row: int = 0,
        apply_ai_mapping: bool = False,
        target_fields: Optional[List[str]] = None,
        **kwargs
    ) -> ParseResult:
        """
        Parse Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to parse (first sheet if None)
            skip_rows: Number of rows to skip at beginning
            header_row: Row number to use as column headers
            apply_ai_mapping: Whether to apply AI column mapping
            target_fields: Target fields for AI mapping

        Returns:
            ParseResult with extracted data
        """
        errors = []
        warnings = []

        try:
            # Determine engine based on file extension
            engine = 'openpyxl' if file_path.suffix.lower() == '.xlsx' else 'xlrd'

            # Read Excel file
            if sheet_name is None:
                # Read first sheet
                df = pd.read_excel(
                    file_path,
                    engine=engine,
                    skiprows=skip_rows,
                    header=header_row,
                    keep_default_na=False,
                    dtype=str
                )
                sheet_name = 'Sheet1'  # Default name
            else:
                df = pd.read_excel(
                    file_path,
                    engine=engine,
                    sheet_name=sheet_name,
                    skiprows=skip_rows,
                    header=header_row,
                    keep_default_na=False,
                    dtype=str
                )

            # Clean column names
            df.columns = df.columns.astype(str).str.strip()

            # Remove completely empty rows
            df = df.dropna(how='all')

            # Convert to list of dicts
            columns = df.columns.tolist()
            data = df.to_dict('records')

            # Apply AI mapping if requested
            if apply_ai_mapping and self.ai_provider and target_fields:
                try:
                    data = await self._apply_ai_mapping(data, columns, target_fields)
                    warnings.append('AI column mapping applied')
                except Exception as e:
                    warnings.append(f'AI mapping failed: {str(e)}')

            # Check data quality with AI
            if self.ai_provider:
                try:
                    quality_issues = await self._check_data_quality(data)
                    warnings.extend(quality_issues)
                except Exception as e:
                    warnings.append(f'Quality check failed: {str(e)}')

            return ParseResult(
                success=True,
                data=data,
                columns=columns,
                row_count=len(data),
                file_type='excel',
                errors=errors,
                warnings=warnings,
                metadata={
                    'sheet_name': sheet_name,
                    'skip_rows': skip_rows,
                    'header_row': header_row,
                    'engine': engine,
                    'original_columns': columns
                }
            )

        except Exception as e:
            errors.append(f'Excel parsing error: {str(e)}')
            return ParseResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                file_type='excel',
                errors=errors
            )

    async def get_sheet_names(self, file_path: Path) -> List[str]:
        """
        Get all sheet names in Excel file.

        Args:
            file_path: Path to Excel file

        Returns:
            List of sheet names
        """
        try:
            engine = 'openpyxl' if file_path.suffix.lower() == '.xlsx' else 'xlrd'
            xl_file = pd.ExcelFile(file_path, engine=engine)
            return xl_file.sheet_names
        except Exception:
            return []
