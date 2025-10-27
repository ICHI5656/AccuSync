"""Claude Provider Implementation"""

import json
from typing import Dict, List, Optional, Any

from anthropic import AsyncAnthropic

from app.ai.base import (
    AIProvider,
    FileDetectionResult,
    DataExtractionResult,
    MappingResult,
    QualityCheckResult
)
from app.core.config import settings


class ClaudeProvider(AIProvider):
    """Anthropic Claude を使用したAIプロバイダー

    長文処理と複雑な文書解析に優れる
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = config.get("model", "claude-3-5-sonnet-20241022")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4000)

    async def detect_file_format(
        self,
        file_content: bytes,
        file_name: str,
        file_extension: Optional[str] = None
    ) -> FileDetectionResult:
        """ファイル形式を検出

        OpenAIProviderと同じロジックを使用
        """
        ext_map = {
            ".csv": "csv",
            ".xlsx": "excel",
            ".xls": "excel",
            ".pdf": "pdf",
            ".txt": "txt",
            ".jpg": "image",
            ".jpeg": "image",
            ".png": "image"
        }

        if file_extension:
            file_type = ext_map.get(file_extension.lower(), "unknown")
            return FileDetectionResult(
                file_type=file_type,
                confidence=0.9 if file_type != "unknown" else 0.3,
                metadata={"source": "extension"}
            )

        for ext, ftype in ext_map.items():
            if file_name.lower().endswith(ext):
                return FileDetectionResult(
                    file_type=ftype,
                    confidence=0.9,
                    metadata={"source": "filename"}
                )

        return FileDetectionResult(
            file_type="unknown",
            confidence=0.0,
            metadata={"source": "fallback"}
        )

    async def extract_data(
        self,
        content: str,
        file_type: str,
        extract_fields: List[str]
    ) -> DataExtractionResult:
        """Claude で非構造化データから情報を抽出"""

        system_prompt = """あなたは注文データ抽出の専門家です。
与えられた文書から注文情報を正確に抽出してください。

抽出する情報：
- order_no: 注文番号
- order_date: 注文日（YYYY-MM-DD形式）
- customer_name: 顧客名
- customer_code: 顧客コード（あれば）
- sku: 商品コード
- product_name: 商品名
- qty: 数量（数値）
- unit_price: 単価（あれば）
- shipping_address: 配送先住所（あれば）
- memo: 備考（あれば）

JSON形式で配列として返してください。"""

        user_prompt = f"""以下の文書から注文情報を抽出してください：

{content}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            result_text = response.content[0].text

            # JSON部分を抽出（```json ... ``` で囲まれている場合）
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()

            parsed_data = json.loads(result_text)

            # データが配列でない場合は配列に変換
            if isinstance(parsed_data, dict):
                if "orders" in parsed_data:
                    data_list = parsed_data["orders"]
                elif "data" in parsed_data:
                    data_list = parsed_data["data"]
                else:
                    data_list = [parsed_data]
            else:
                data_list = parsed_data if isinstance(parsed_data, list) else [parsed_data]

            return DataExtractionResult(
                success=True,
                data=data_list,
                confidence=0.9,
                errors=None
            )

        except Exception as e:
            return DataExtractionResult(
                success=False,
                data=[],
                confidence=0.0,
                errors=[str(e)]
            )

    async def auto_map_columns(
        self,
        column_names: List[str],
        target_fields: List[str],
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> MappingResult:
        """列名を自動マッピング"""

        system_prompt = """あなたはデータマッピングの専門家です。
CSVやExcelの列名を適切なフィールドにマッピングしてください。

日本語の列名にも対応してください。
JSON形式でマッピングを返してください。"""

        user_prompt = f"""以下の列名を適切なフィールドにマッピングしてください：

列名: {', '.join(column_names)}

対象フィールド: {', '.join(target_fields)}

例: {{"列名": "フィールド名", ...}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            result_text = response.content[0].text

            # JSON部分を抽出
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()

            mapping = json.loads(result_text)

            if "mapping" in mapping:
                mapping = mapping["mapping"]

            return MappingResult(
                success=True,
                mapping=mapping,
                confidence=0.85,
                suggestions=None
            )

        except Exception as e:
            return MappingResult(
                success=False,
                mapping={},
                confidence=0.0,
                suggestions=None
            )

    async def check_data_quality(
        self,
        data: List[Dict[str, Any]],
        rules: Optional[Dict[str, Any]] = None
    ) -> QualityCheckResult:
        """データ品質チェックと補完"""

        system_prompt = """あなたはデータ品質チェックの専門家です。
与えられたデータの品質をチェックし、問題点と修正提案、補完後のデータを返してください。

JSON形式で返してください。"""

        user_prompt = f"""以下のデータをチェックしてください：

{json.dumps(data[:10], ensure_ascii=False, indent=2)}

以下の形式で返してください：
{{
  "issues": [問題リスト],
  "suggestions": [修正提案リスト],
  "enhanced_data": [補完後のデータ]
}}"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            result_text = response.content[0].text

            # JSON部分を抽出
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()

            result = json.loads(result_text)

            return QualityCheckResult(
                success=True,
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", []),
                enhanced_data=result.get("enhanced_data", data)
            )

        except Exception as e:
            return QualityCheckResult(
                success=False,
                issues=[{"error": str(e)}],
                suggestions=[],
                enhanced_data=None
            )
