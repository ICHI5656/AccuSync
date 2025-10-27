"""OpenAI Provider Implementation"""

import json
from typing import Dict, List, Optional, Any

from openai import AsyncOpenAI

from app.ai.base import (
    AIProvider,
    FileDetectionResult,
    DataExtractionResult,
    MappingResult,
    QualityCheckResult,
    CustomerTypeResult
)
from app.core.config import settings


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4o を使用したAIプロバイダー

    Structured Outputsを活用した高精度なデータ抽出を実現
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = config.get("model", "gpt-4o")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens = config.get("max_tokens", 4000)

    async def detect_file_format(
        self,
        file_content: bytes,
        file_name: str,
        file_extension: Optional[str] = None
    ) -> FileDetectionResult:
        """ファイル形式を検出"""

        # 簡易的な実装（拡張子ベース）
        # 本格実装ではファイルコンテンツを解析
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

        # ファイル名から拡張子を取得
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
        """OpenAI GPT-4oで非構造化データから情報を抽出"""

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

複数の注文が含まれる場合は、それぞれを別のオブジェクトとして抽出してください。
"""

        user_prompt = f"""以下の文書から注文情報を抽出してください：

{content}

JSON形式で配列として返してください。"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
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
例:
- "注文番号" → "order_no"
- "注文日" → "order_date"
- "顧客名" → "customer_name"
- "商品コード" → "sku"
- "商品名" → "product_name"
- "数量" → "qty"
- "単価" → "unit_price"
"""

        user_prompt = f"""以下の列名を適切なフィールドにマッピングしてください：

列名: {', '.join(column_names)}

対象フィールド: {', '.join(target_fields)}

JSON形式でマッピングを返してください。
例: {{"列名": "フィールド名", ...}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            mapping = json.loads(result_text)

            # mappingキーでラップされている場合は展開
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
与えられたデータの品質をチェックし、問題点と修正提案を返してください。

チェック項目：
1. 必須フィールドの欠損
2. データ型の不一致
3. 日付フォーマットの統一
4. 数値フォーマットの統一
5. 異常値の検出
6. 重複データの検出

修正可能な問題は自動的に補完してください。
"""

        user_prompt = f"""以下のデータをチェックしてください：

{json.dumps(data[:10], ensure_ascii=False, indent=2)}

JSON形式で以下を返してください：
{{
  "issues": [問題リスト],
  "suggestions": [修正提案リスト],
  "enhanced_data": [補完後のデータ]
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
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

    async def classify_customer_type(
        self,
        customer_name: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> CustomerTypeResult:
        """顧客名から会社か個人かを判定"""

        system_prompt = """あなたは日本の商習慣に精通したビジネスデータ分析の専門家です。
顧客名から、それが「法人（会社）」か「個人」かを判定してください。

判定基準：
1. 法人の特徴：
   - 「株式会社」「合同会社」「有限会社」などの法人格が含まれる
   - 「〜会社」「〜法人」「〜組合」などの語尾
   - 「〜商店」「〜工房」「〜事務所」「〜スタジオ」など事業名
   - カタカナのみの企業名

2. 個人の特徴：
   - 姓名の組み合わせ（例：山田太郎、佐藤花子）
   - 「様」「さん」などの敬称が付いている
   - 漢字2〜4文字程度で人名として自然
   - フリガナや個人を示す情報がある

3. 判定が難しい場合：
   - 屋号のみの場合は個人事業主として「個人」扱い
   - 不明な場合は法人と判定（安全側）

必ず信頼度（0.0〜1.0）と判定理由も返してください。
"""

        # 追加情報を含めたプロンプト作成
        additional_context = ""
        if additional_info:
            if additional_info.get('address'):
                additional_context += f"\n住所: {additional_info['address']}"
            if additional_info.get('phone'):
                additional_context += f"\n電話番号: {additional_info['phone']}"
            if additional_info.get('email'):
                additional_context += f"\nメール: {additional_info['email']}"

        user_prompt = f"""以下の顧客名が「法人（会社）」か「個人」かを判定してください：

顧客名: {customer_name}{additional_context}

JSON形式で以下を返してください：
{{
  "is_individual": true/false,
  "confidence": 0.0〜1.0,
  "reason": "判定理由"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 一貫性のため低温度
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            return CustomerTypeResult(
                is_individual=result.get("is_individual", False),
                confidence=result.get("confidence", 0.8),
                reason=result.get("reason", ""),
                metadata=additional_info
            )

        except Exception as e:
            # エラー時は安全側（法人）として判定
            return CustomerTypeResult(
                is_individual=False,
                confidence=0.5,
                reason=f"AI判定エラー: {str(e)}。デフォルトで法人として扱います。",
                metadata=additional_info
            )
