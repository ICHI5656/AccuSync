"""列マッピングフィールド定義"""

from typing import Dict, List

# 標準フィールド定義
STANDARD_FIELDS: Dict[str, Dict[str, any]] = {
    # 必須フィールド
    "customer_name": {
        "label": "顧客名",
        "required": True,
        "description": "取引先の会社名または個人名",
        "aliases": ["顧客名", "受注先名", "お客様名", "取引先名", "会社名", "氏名", "customer", "client_name"]
    },
    "product_name": {
        "label": "商品名",
        "required": True,
        "description": "商品またはサービスの名称",
        "aliases": ["商品名", "品名", "サービス名", "product", "item_name", "service"]
    },
    "quantity": {
        "label": "数量",
        "required": True,
        "description": "注文数量",
        "aliases": ["数量", "個数", "qty", "quantity", "amount", "count"]
    },
    "unit_price": {
        "label": "単価",
        "required": True,
        "description": "商品の単価（税抜）",
        "aliases": ["単価", "価格", "unit_price", "price", "unit_cost"]
    },

    # 顧客情報（オプション）
    "customer_code": {
        "label": "顧客コード",
        "required": False,
        "description": "顧客の識別コード",
        "aliases": ["顧客コード", "得意先コード", "customer_code", "client_code"]
    },
    "address": {
        "label": "住所",
        "required": False,
        "description": "顧客の住所",
        "aliases": ["住所", "所在地", "address", "location"]
    },
    "postal_code": {
        "label": "郵便番号",
        "required": False,
        "description": "郵便番号",
        "aliases": ["郵便番号", "〒", "postal_code", "zip", "zipcode", "post_code"]
    },
    "phone": {
        "label": "電話番号",
        "required": False,
        "description": "連絡先電話番号",
        "aliases": ["電話番号", "TEL", "電話", "phone", "tel", "telephone"]
    },
    "email": {
        "label": "メールアドレス",
        "required": False,
        "description": "連絡先メールアドレス",
        "aliases": ["メールアドレス", "メール", "E-mail", "email", "mail"]
    },

    # 商品情報（オプション）
    "product_sku": {
        "label": "商品コード",
        "required": False,
        "description": "商品の識別コード（SKU）",
        "aliases": ["商品コード", "品番", "SKU", "product_code", "item_code", "sku"]
    },
    "product_category": {
        "label": "商品カテゴリ",
        "required": False,
        "description": "商品の分類カテゴリ",
        "aliases": ["カテゴリ", "分類", "category"]
    },

    # 注文情報（オプション）
    "order_no": {
        "label": "注文番号",
        "required": False,
        "description": "注文の識別番号",
        "aliases": ["注文番号", "受注番号", "order_no", "order_number", "po_number"]
    },
    "order_date": {
        "label": "注文日",
        "required": False,
        "description": "注文を受けた日付",
        "aliases": ["注文日", "受注日", "order_date", "date", "受付日"]
    },
    "delivery_date": {
        "label": "納品日",
        "required": False,
        "description": "納品予定日または納品済み日",
        "aliases": ["納品日", "配送日", "delivery_date", "shipping_date", "出荷日"]
    },

    # 金額情報（オプション）
    "subtotal": {
        "label": "小計",
        "required": False,
        "description": "税抜きの小計金額",
        "aliases": ["小計", "合計", "subtotal", "amount", "税抜金額"]
    },
    "tax_rate": {
        "label": "税率",
        "required": False,
        "description": "消費税率（例: 0.1 = 10%）",
        "aliases": ["税率", "消費税率", "tax_rate", "vat_rate"]
    },
    "tax_amount": {
        "label": "税額",
        "required": False,
        "description": "消費税額",
        "aliases": ["税額", "消費税", "tax", "tax_amount", "vat"]
    },
    "total": {
        "label": "合計（税込）",
        "required": False,
        "description": "税込みの合計金額",
        "aliases": ["合計", "税込金額", "total", "total_amount", "税込"]
    },

    # その他（オプション）
    "notes": {
        "label": "備考",
        "required": False,
        "description": "メモや特記事項",
        "aliases": ["備考", "メモ", "特記事項", "notes", "remarks", "comment", "memo"]
    },
    "discount": {
        "label": "割引額",
        "required": False,
        "description": "割引金額",
        "aliases": ["割引", "値引き", "discount", "割引額"]
    },
    "shipping_fee": {
        "label": "送料",
        "required": False,
        "description": "配送料金",
        "aliases": ["送料", "配送料", "shipping", "shipping_fee", "delivery_fee"]
    }
}


def get_required_fields() -> List[str]:
    """必須フィールドのリストを取得"""
    return [key for key, value in STANDARD_FIELDS.items() if value["required"]]


def get_optional_fields() -> List[str]:
    """オプションフィールドのリストを取得"""
    return [key for key, value in STANDARD_FIELDS.items() if not value["required"]]


def get_field_label(field_key: str) -> str:
    """フィールドのラベルを取得"""
    return STANDARD_FIELDS.get(field_key, {}).get("label", field_key)


def get_field_description(field_key: str) -> str:
    """フィールドの説明を取得"""
    return STANDARD_FIELDS.get(field_key, {}).get("description", "")


def get_all_field_keys() -> List[str]:
    """すべてのフィールドキーを取得"""
    return list(STANDARD_FIELDS.keys())
