"""Pricing Service - 単価決定サービス"""

from datetime import date
from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.pricing_rule import PricingRule
from app.models.product import Product


class PricingService:
    """単価決定サービス

    会社×商品×数量×期間で最適な単価を決定します
    """

    @staticmethod
    def get_price(
        db: Session,
        customer_id: int,
        product_id: int,
        qty: int,
        order_date: date
    ) -> Decimal:
        """最適な単価を取得

        Args:
            db: Database session
            customer_id: 取引先ID
            product_id: 商品ID
            qty: 数量
            order_date: 注文日

        Returns:
            適用される単価

        ロジック:
            1. 該当する PricingRule を検索（customer_id, product_id, 期間内）
            2. 数量条件（min_qty）を満たすルールにフィルタリング
            3. priority desc, start_date desc でソート
            4. 最初にマッチしたルールの単価を返す
            5. ルールがない場合は商品の default_price を返す
        """

        # 該当するPricingRuleを検索
        rules_query = db.query(PricingRule).filter(
            PricingRule.customer_id == customer_id,
            PricingRule.product_id == product_id
        )

        # 期間フィルタ
        rules_query = rules_query.filter(
            (PricingRule.start_date.is_(None)) | (PricingRule.start_date <= order_date)
        ).filter(
            (PricingRule.end_date.is_(None)) | (PricingRule.end_date >= order_date)
        )

        # 数量フィルタ
        rules_query = rules_query.filter(
            (PricingRule.min_qty.is_(None)) | (PricingRule.min_qty <= qty)
        )

        # 優先度でソート
        rules = rules_query.order_by(
            PricingRule.priority.desc(),
            PricingRule.start_date.desc()
        ).all()

        # 最初にマッチしたルールを使用
        if rules:
            return rules[0].price

        # ルールがない場合は商品の標準単価を返す
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            return product.default_price

        # 商品が見つからない場合は0を返す（エラーケース）
        return Decimal(0)

    @staticmethod
    def calculate_line_total(
        unit_price: Decimal,
        qty: int,
        tax_rate: Decimal,
        discount: Decimal = Decimal(0),
        round_mode: str = "ROUND_HALF_UP"
    ) -> dict:
        """明細行の金額を計算

        Args:
            unit_price: 単価
            qty: 数量
            tax_rate: 税率（例: 0.10 = 10%）
            discount: 割引額（デフォルト: 0）
            round_mode: 端数処理モード（ROUND_DOWN, ROUND_UP, ROUND_HALF_UP）

        Returns:
            計算結果辞書
                - subtotal_ex_tax: 税抜小計
                - tax_amount: 消費税額
                - total_in_tax: 税込合計
        """
        from decimal import ROUND_DOWN, ROUND_UP, ROUND_HALF_UP

        round_modes = {
            "ROUND_DOWN": ROUND_DOWN,
            "ROUND_UP": ROUND_UP,
            "ROUND_HALF_UP": ROUND_HALF_UP,
        }

        rounding = round_modes.get(round_mode, ROUND_HALF_UP)

        # 税抜小計 = (単価 × 数量) - 割引
        subtotal_ex_tax = (unit_price * qty) - discount
        subtotal_ex_tax = subtotal_ex_tax.quantize(Decimal('1'), rounding=rounding)

        # 消費税額 = 税抜小計 × 税率
        tax_amount = (subtotal_ex_tax * tax_rate).quantize(Decimal('1'), rounding=rounding)

        # 税込合計 = 税抜小計 + 消費税額
        total_in_tax = subtotal_ex_tax + tax_amount

        return {
            "subtotal_ex_tax": subtotal_ex_tax,
            "tax_amount": tax_amount,
            "total_in_tax": total_in_tax
        }
