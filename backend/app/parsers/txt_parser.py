"""
Text file parser with AI-based data extraction.
Handles unstructured text like notes, emails, or plain text orders.
"""

import chardet
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import FileParser, ParseResult


class TXTParser(FileParser):
    """
    Parser for plain text files.
    Uses AI to extract structured data from unstructured text.
    """

    SUPPORTED_EXTENSIONS = ['.txt', '.text']
    COMMON_ENCODINGS = ['utf-8', 'shift-jis', 'cp932', 'euc-jp', 'iso-2022-jp']

    def validate(self, file_path: Path) -> bool:
        """Validate if file is text format."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    async def parse(
        self,
        file_path: Path,
        encoding: Optional[str] = None,
        target_fields: Optional[List[str]] = None,
        **kwargs
    ) -> ParseResult:
        """
        Parse text file using AI extraction.

        Args:
            file_path: Path to text file
            encoding: Optional encoding (auto-detected if None)
            target_fields: Fields to extract using AI

        Returns:
            ParseResult with extracted data
        """
        errors = []
        warnings = []

        try:
            # Detect encoding if not provided
            if encoding is None:
                encoding = self._detect_encoding(file_path)
                if encoding is None:
                    encoding = self._try_common_encodings(file_path)
                    if encoding is None:
                        return ParseResult(
                            success=False,
                            data=[],
                            columns=[],
                            row_count=0,
                            file_type='txt',
                            errors=['Failed to detect file encoding']
                        )

            # Read text content
            with open(file_path, 'r', encoding=encoding) as f:
                text_content = f.read()

            if not text_content.strip():
                return ParseResult(
                    success=False,
                    data=[],
                    columns=[],
                    row_count=0,
                    file_type='txt',
                    errors=['Empty text file']
                )

            # Use AI to extract structured data
            if not self.ai_provider:
                warnings.append('AI provider not available - returning raw text')
                data = [{'raw_text': text_content}]
                columns = ['raw_text']
            else:
                try:
                    # Define default fields if not provided
                    if not target_fields:
                        target_fields = [
                            '顧客名', '住所', '郵便番号', '電話番号',
                            '商品名', '機種', 'デザイン', '数量',
                            '単価', '金額', '納期', '備考'
                        ]

                    extraction_result = await self.ai_provider.extract_data(
                        content=text_content,
                        file_type='txt',
                        extract_fields=target_fields
                    )

                    if extraction_result.success and extraction_result.data:
                        data = extraction_result.data
                        columns = list(data[0].keys()) if data else []
                    else:
                        warnings.append('AI extraction returned no data - using raw text')
                        data = [{'raw_text': text_content}]
                        columns = ['raw_text']

                except Exception as e:
                    warnings.append(f'AI extraction failed: {str(e)} - using raw text')
                    data = [{'raw_text': text_content}]
                    columns = ['raw_text']

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
                file_type='txt',
                encoding=encoding,
                errors=errors,
                warnings=warnings,
                metadata={
                    'text_length': len(text_content),
                    'ai_extracted': self.ai_provider is not None
                }
            )

        except Exception as e:
            errors.append(f'Text parsing error: {str(e)}')
            return ParseResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                file_type='txt',
                encoding=encoding,
                errors=errors
            )

    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """Detect file encoding using chardet."""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                if result['confidence'] > 0.7:
                    return result['encoding']
        except Exception:
            pass
        return None

    def _try_common_encodings(self, file_path: Path) -> Optional[str]:
        """Try common encodings to read file."""
        for encoding in self.COMMON_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None
