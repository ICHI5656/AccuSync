"""
PDF file parser with text extraction.
"""

import pdfplumber
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import FileParser, ParseResult


class PDFParser(FileParser):
    """
    Parser for PDF files with text extraction.
    Uses AI for extracting structured data from unstructured PDF content.
    """

    SUPPORTED_EXTENSIONS = ['.pdf']

    def validate(self, file_path: Path) -> bool:
        """Validate if file is PDF."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    async def parse(
        self,
        file_path: Path,
        extract_tables: bool = True,
        extract_text: bool = True,
        target_fields: Optional[List[str]] = None,
        **kwargs
    ) -> ParseResult:
        """
        Parse PDF file and extract data.

        Args:
            file_path: Path to PDF file
            extract_tables: Whether to extract tables
            extract_text: Whether to extract text
            target_fields: Fields to extract using AI

        Returns:
            ParseResult with extracted data
        """
        errors = []
        warnings = []
        all_data = []
        columns = []

        try:
            with pdfplumber.open(file_path) as pdf:
                # Extract from all pages
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract tables if requested
                    if extract_tables:
                        tables = page.extract_tables()
                        for table_num, table in enumerate(tables):
                            if table and len(table) > 1:
                                # Use first row as headers
                                headers = [str(h).strip() if h else f'Column_{i}'
                                          for i, h in enumerate(table[0])]

                                # Convert table to list of dicts
                                for row in table[1:]:
                                    if row:
                                        row_data = {}
                                        for i, value in enumerate(row):
                                            if i < len(headers):
                                                row_data[headers[i]] = str(value).strip() if value else ''
                                        if any(row_data.values()):  # Skip empty rows
                                            row_data['_page'] = page_num
                                            row_data['_table'] = table_num
                                            all_data.append(row_data)

                                # Update columns
                                for header in headers:
                                    if header not in columns:
                                        columns.append(header)

                    # Extract text if requested and use AI for extraction
                    if extract_text and self.ai_provider:
                        text = page.extract_text()
                        if text:
                            try:
                                # Use AI to extract structured data from text
                                extraction_result = await self.ai_provider.extract_data(
                                    content=text,
                                    file_type='pdf',
                                    extract_fields=target_fields or []
                                )

                                if extraction_result.success and extraction_result.data:
                                    for item in extraction_result.data:
                                        item['_page'] = page_num
                                        item['_source'] = 'text_extraction'
                                        all_data.append(item)

                                    # Update columns
                                    for item in extraction_result.data:
                                        for key in item.keys():
                                            if key not in columns:
                                                columns.append(key)

                            except Exception as e:
                                warnings.append(f'AI extraction failed on page {page_num}: {str(e)}')

            # Add metadata columns if not present
            if '_page' not in columns:
                columns.insert(0, '_page')

            # Check data quality with AI
            if self.ai_provider and all_data:
                try:
                    quality_issues = await self._check_data_quality(all_data)
                    warnings.extend(quality_issues)
                except Exception as e:
                    warnings.append(f'Quality check failed: {str(e)}')

            success = len(all_data) > 0
            if not success:
                warnings.append('No data extracted from PDF')

            return ParseResult(
                success=success,
                data=all_data,
                columns=columns,
                row_count=len(all_data),
                file_type='pdf',
                errors=errors,
                warnings=warnings,
                metadata={
                    'pages': len(pdf.pages),
                    'extract_tables': extract_tables,
                    'extract_text': extract_text
                }
            )

        except Exception as e:
            errors.append(f'PDF parsing error: {str(e)}')
            return ParseResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                file_type='pdf',
                errors=errors
            )
