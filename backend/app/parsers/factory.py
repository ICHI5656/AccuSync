"""
File parser factory for creating appropriate parser based on file type.
"""

from pathlib import Path
from typing import Optional

from .base import FileParser
from .csv_parser import CSVParser
from .excel_parser import ExcelParser
from .pdf_parser import PDFParser
from .txt_parser import TXTParser


class FileParserFactory:
    """
    Factory for creating appropriate file parser based on file extension.
    """

    _PARSER_MAP = {
        '.csv': CSVParser,
        '.xlsx': ExcelParser,
        '.xls': ExcelParser,
        '.xlsm': ExcelParser,
        '.pdf': PDFParser,
        '.txt': TXTParser,
        '.text': TXTParser,
    }

    @classmethod
    def create_parser(
        cls,
        file_path: Path,
        ai_provider=None
    ) -> Optional[FileParser]:
        """
        Create appropriate parser for file.

        Args:
            file_path: Path to file
            ai_provider: Optional AI provider for enhanced parsing

        Returns:
            FileParser instance or None if format not supported
        """
        extension = file_path.suffix.lower()
        parser_class = cls._PARSER_MAP.get(extension)

        if parser_class is None:
            return None

        return parser_class(ai_provider=ai_provider)

    @classmethod
    def get_supported_extensions(cls) -> list:
        """
        Get list of supported file extensions.

        Returns:
            List of supported extensions
        """
        return list(cls._PARSER_MAP.keys())

    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        extension = file_path.suffix.lower()
        return extension in cls._PARSER_MAP

    @classmethod
    def detect_file_type(cls, file_path: Path) -> str:
        """
        Detect file type from extension.

        Args:
            file_path: Path to file

        Returns:
            File type name (csv, excel, pdf, txt) or 'unknown'
        """
        extension = file_path.suffix.lower()

        if extension == '.csv':
            return 'csv'
        elif extension in ['.xlsx', '.xls', '.xlsm']:
            return 'excel'
        elif extension == '.pdf':
            return 'pdf'
        elif extension in ['.txt', '.text']:
            return 'txt'
        else:
            return 'unknown'
