"""
Field mapping schemas for standardizing column names.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class StandardField(BaseModel):
    """Standard field definition."""
    key: str = Field(..., description="Internal field key")
    label: str = Field(..., description="Display label (Japanese)")
    description: str = Field(..., description="Field description")
    required: bool = Field(default=False, description="Whether field is required")
    data_type: str = Field(default="string", description="Expected data type")


# 標準フィールド定義
STANDARD_FIELDS: List[StandardField] = [
    StandardField(
        key="customer_name",
        label="顧客名",
        description="取引先会社名または個人名",
        required=True,
        data_type="string"
    ),
    StandardField(
        key="product_name",
        label="商品名",
        description="商品・サービス名称",
        required=True,
        data_type="string"
    ),
    StandardField(
        key="quantity",
        label="数量",
        description="注文数量",
        required=True,
        data_type="number"
    ),
    StandardField(
        key="unit_price",
        label="単価",
        description="商品単価（税抜）",
        required=True,
        data_type="number"
    ),
    StandardField(
        key="order_date",
        label="注文日",
        description="注文日時",
        required=False,
        data_type="date"
    ),
    StandardField(
        key="address",
        label="住所",
        description="顧客住所",
        required=False,
        data_type="string"
    ),
    StandardField(
        key="postal_code",
        label="郵便番号",
        description="顧客郵便番号",
        required=False,
        data_type="string"
    ),
    StandardField(
        key="phone",
        label="電話番号",
        description="顧客電話番号",
        required=False,
        data_type="string"
    ),
    StandardField(
        key="email",
        label="メールアドレス",
        description="顧客メールアドレス",
        required=False,
        data_type="string"
    ),
    StandardField(
        key="notes",
        label="備考",
        description="注文に関する備考・メモ",
        required=False,
        data_type="string"
    ),
]


# よくある列名の自動マッピング候補
COMMON_COLUMN_PATTERNS: Dict[str, List[str]] = {
    "customer_name": [
        "顧客名", "お客様名", "取引先名", "受注先名", "会社名", "氏名", "注文者氏名", "送付先氏名",
        "customer_name", "customer", "client_name", "client", "company_name", "name"
    ],
    "product_name": [
        "商品名", "品名", "製品名", "機種", "アイテム名", "サービス名",
        "product_name", "product", "item_name", "item", "model", "service"
    ],
    "quantity": [
        "数量", "個数", "数", "qty", "quantity", "count", "amount", "number"
    ],
    "unit_price": [
        "単価", "価格", "金額", "販売価格", "unit_price", "price", "cost", "amount"
    ],
    "order_date": [
        "注文日", "受注日", "注文日時", "受注日時", "発注日", "日付",
        "order_date", "order_datetime", "date", "ordered_at", "created_at"
    ],
    "address": [
        "住所", "所在地", "注文者住所", "送付先住所", "address", "location"
    ],
    "postal_code": [
        "郵便番号", "〒", "注文者郵便番号", "送付先郵便番号", "postal_code", "zip_code", "zip", "postal"
    ],
    "phone": [
        "電話番号", "電話", "TEL", "tel", "注文者電話番号", "送付先電話番号", "phone", "phone_number", "contact"
    ],
    "email": [
        "メールアドレス", "メール", "Eメール", "email", "e-mail", "mail"
    ],
    "notes": [
        "備考", "メモ", "注記", "コメント", "notes", "memo", "comment", "remarks"
    ]
}


class AutoMappingResult(BaseModel):
    """Result of automatic column mapping."""
    mapping: Dict[str, str] = Field(..., description="Suggested mapping (standard_field -> source_column)")
    confidence: Dict[str, float] = Field(default_factory=dict, description="Confidence score for each mapping")
    unmapped_columns: List[str] = Field(default_factory=list, description="Source columns not mapped")
    missing_required_fields: List[str] = Field(default_factory=list, description="Required fields without mapping")


def auto_map_columns(source_columns: List[str]) -> AutoMappingResult:
    """
    Automatically map source columns to standard fields.

    Args:
        source_columns: List of column names from uploaded file

    Returns:
        AutoMappingResult with suggested mappings
    """
    mapping: Dict[str, str] = {}
    confidence: Dict[str, float] = {}
    unmapped_columns = list(source_columns)

    # 各標準フィールドに対してマッチングを試みる
    for standard_field_key, patterns in COMMON_COLUMN_PATTERNS.items():
        for source_col in source_columns:
            source_col_lower = source_col.lower().strip()

            # 完全一致チェック
            for pattern in patterns:
                pattern_lower = pattern.lower().strip()

                if source_col_lower == pattern_lower:
                    mapping[standard_field_key] = source_col
                    confidence[standard_field_key] = 1.0
                    if source_col in unmapped_columns:
                        unmapped_columns.remove(source_col)
                    break

                # 部分一致チェック（信頼度を下げる）
                elif pattern_lower in source_col_lower or source_col_lower in pattern_lower:
                    # 既にマッピングされていない場合のみ
                    if standard_field_key not in mapping:
                        mapping[standard_field_key] = source_col
                        confidence[standard_field_key] = 0.7
                        if source_col in unmapped_columns:
                            unmapped_columns.remove(source_col)

            if standard_field_key in mapping:
                break

    # 必須フィールドのチェック
    missing_required_fields = [
        field.key for field in STANDARD_FIELDS
        if field.required and field.key not in mapping
    ]

    return AutoMappingResult(
        mapping=mapping,
        confidence=confidence,
        unmapped_columns=unmapped_columns,
        missing_required_fields=missing_required_fields
    )
