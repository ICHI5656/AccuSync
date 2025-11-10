"""
CSV file parser with automatic encoding detection.
"""

import csv
import chardet
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from .base import FileParser, ParseResult
from app.services.device_detection_service import DeviceDetectionService


class CSVParser(FileParser):
    """
    Parser for CSV files with automatic encoding detection.
    Supports various encodings (UTF-8, Shift-JIS, etc.)
    """

    SUPPORTED_EXTENSIONS = ['.csv']
    COMMON_ENCODINGS = ['utf-8', 'shift-jis', 'cp932', 'euc-jp', 'iso-2022-jp']

    def validate(self, file_path: Path) -> bool:
        """Validate if file is CSV."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    async def parse(
        self,
        file_path: Path,
        encoding: Optional[str] = None,
        delimiter: str = ',',
        skip_rows: int = 0,
        apply_ai_mapping: bool = False,
        target_fields: Optional[List[str]] = None,
        db_session: Optional[Session] = None,
        **kwargs
    ) -> ParseResult:
        """
        Parse CSV file with automatic encoding detection.

        Args:
            file_path: Path to CSV file
            encoding: Optional encoding (auto-detected if None)
            delimiter: CSV delimiter (default: ',')
            skip_rows: Number of rows to skip at beginning
            apply_ai_mapping: Whether to apply AI column mapping
            target_fields: Target fields for AI mapping

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
                    # Try common encodings
                    encoding = self._try_common_encodings(file_path)
                    if encoding is None:
                        return ParseResult(
                            success=False,
                            data=[],
                            columns=[],
                            row_count=0,
                            file_type='csv',
                            errors=['Failed to detect file encoding']
                        )

            # Read CSV with pandas
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                skiprows=skip_rows,
                keep_default_na=False,
                dtype=str  # Read all as strings initially
            )

            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()

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

            # Apply device detection to all rows
            if db_session:
                try:
                    detector = DeviceDetectionService(db_session)
                    for row in data:
                        # Detect device from row
                        device, detection_method, brand = detector.detect_device_from_row(row)

                        # Extract size from row (prioritize options column)
                        product_name = row.get('商品名', '') or row.get('product_name', '')
                        product_type = row.get('extracted_memo', '')
                        size, size_method = detector.extract_size_from_product_name(
                            product_name=product_name,
                            product_type=product_type,
                            brand=brand,
                            device=device,
                            row=row  # Pass row to check options column
                        )

                        # Store detected values in row
                        row['detected_brand'] = brand or ''
                        row['detected_device'] = device or ''
                        row['detected_size'] = size or '-'
                        row['detection_method'] = detection_method or ''
                        row['size_detection_method'] = size_method or ''

                    warnings.append(f'Device detection applied to {len(data)} rows')
                except Exception as e:
                    warnings.append(f'Device detection failed: {str(e)}')

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
                file_type='csv',
                encoding=encoding,
                errors=errors,
                warnings=warnings,
                metadata={
                    'delimiter': delimiter,
                    'skip_rows': skip_rows,
                    'original_columns': columns
                }
            )

        except Exception as e:
            errors.append(f'CSV parsing error: {str(e)}')
            return ParseResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                file_type='csv',
                encoding=encoding,
                errors=errors
            )

    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """
        Detect file encoding using chardet.

        Args:
            file_path: Path to file

        Returns:
            Detected encoding or None
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                if result['confidence'] > 0.7:
                    return result['encoding']
        except Exception:
            pass
        return None

    def _try_common_encodings(self, file_path: Path) -> Optional[str]:
        """
        Try common encodings to read file.

        Args:
            file_path: Path to file

        Returns:
            Working encoding or None
        """
        for encoding in self.COMMON_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1000)  # Try to read 1000 chars
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None
