"""
Base parser class and common utilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ParseResult:
    """
    Result of file parsing operation.
    """

    success: bool
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    file_type: str
    encoding: Optional[str] = None
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class FileParser(ABC):
    """
    Abstract base class for file parsers.
    """

    def __init__(self, ai_provider=None):
        """
        Initialize parser with optional AI provider.

        Args:
            ai_provider: AI provider instance for data extraction/mapping
        """
        self.ai_provider = ai_provider

    @abstractmethod
    async def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """
        Parse file and extract data.

        Args:
            file_path: Path to file to parse
            **kwargs: Additional parser-specific options

        Returns:
            ParseResult with extracted data
        """
        pass

    @abstractmethod
    def validate(self, file_path: Path) -> bool:
        """
        Validate if file can be parsed by this parser.

        Args:
            file_path: Path to file to validate

        Returns:
            True if file can be parsed
        """
        pass

    async def _apply_ai_mapping(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        target_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Apply AI-based column mapping to data.

        Args:
            data: Raw data from file
            columns: Column names from file
            target_fields: Target field names for mapping

        Returns:
            Data with mapped column names
        """
        if not self.ai_provider:
            return data

        # Use AI to map columns
        mapping_result = await self.ai_provider.auto_map_columns(
            column_names=columns,
            target_fields=target_fields
        )

        if not mapping_result.success:
            return data

        # Apply mapping
        mapped_data = []
        for row in data:
            mapped_row = {}
            for target_field, source_column in mapping_result.mappings.items():
                if source_column in row:
                    mapped_row[target_field] = row[source_column]
            mapped_data.append(mapped_row)

        return mapped_data

    async def _check_data_quality(
        self,
        data: List[Dict[str, Any]],
        rules: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Check data quality using AI.

        Args:
            data: Data to check
            rules: Optional quality rules

        Returns:
            List of warnings/issues found
        """
        if not self.ai_provider:
            return []

        quality_result = await self.ai_provider.check_data_quality(
            data=data,
            rules=rules
        )

        return quality_result.issues if quality_result.success else []
