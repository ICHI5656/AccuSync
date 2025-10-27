#!/usr/bin/env python3
"""
Test script for file parsers with testdata.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.parsers.factory import FileParserFactory
from app.ai.factory import AIProviderFactory


async def test_parser(file_path: Path):
    """Test parser with given file."""
    print(f"\n{'='*60}")
    print(f"Testing: {file_path.name}")
    print(f"{'='*60}")

    # Check if file is supported
    if not FileParserFactory.is_supported(file_path):
        print(f"❌ Unsupported file format: {file_path.suffix}")
        return

    file_type = FileParserFactory.detect_file_type(file_path)
    print(f"📄 File type: {file_type}")

    # Create AI provider
    try:
        ai_provider = AIProviderFactory.create()
        print(f"✅ AI Provider: {ai_provider.__class__.__name__}")
    except Exception as e:
        print(f"⚠️  AI Provider not available: {e}")
        ai_provider = None

    # Create parser
    parser = FileParserFactory.create_parser(file_path, ai_provider=ai_provider)
    print(f"✅ Parser: {parser.__class__.__name__}")

    # Parse file
    try:
        print(f"\n🔄 Parsing file...")
        result = await parser.parse(
            file_path=file_path,
            apply_ai_mapping=True,
            target_fields=[
                '顧客名', '住所', '郵便番号', '電話番号',
                '商品名', '機種', 'デザイン', '数量',
                '単価', '金額', '納期', '備考'
            ]
        )

        if result.success:
            print(f"✅ Parsing successful!")
            print(f"\n📊 Results:")
            print(f"   - Rows: {result.row_count}")
            print(f"   - Columns: {len(result.columns)}")
            if result.encoding:
                print(f"   - Encoding: {result.encoding}")

            print(f"\n📋 Columns:")
            for col in result.columns:
                print(f"   - {col}")

            if result.warnings:
                print(f"\n⚠️  Warnings:")
                for warn in result.warnings:
                    print(f"   - {warn}")

            if result.errors:
                print(f"\n❌ Errors:")
                for err in result.errors:
                    print(f"   - {err}")

            # Show first few rows
            if result.data:
                print(f"\n🔍 Sample Data (first 3 rows):")
                for i, row in enumerate(result.data[:3], 1):
                    print(f"\n   Row {i}:")
                    for key, value in list(row.items())[:5]:  # Limit columns shown
                        if value:
                            print(f"      {key}: {value}")
        else:
            print(f"❌ Parsing failed!")
            for err in result.errors:
                print(f"   - {err}")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    testdata_dir = Path(__file__).parent / "testdata"

    if not testdata_dir.exists():
        print(f"❌ Testdata directory not found: {testdata_dir}")
        return

    # Test specific files
    test_files = [
        "2025-10-17注文書.csv",
        "251010株式会社Quest様注文書.xlsx",
        "クエスト発注書2024.2.29.pdf",
        "青江注文.txt",
    ]

    for filename in test_files:
        file_path = testdata_dir / filename
        if file_path.exists():
            await test_parser(file_path)
        else:
            print(f"⚠️  File not found: {filename}")

    print(f"\n{'='*60}")
    print("✅ All tests completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
