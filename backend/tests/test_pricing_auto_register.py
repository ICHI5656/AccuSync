"""
Tests for automatic pricing rule registration functionality.

このテストは、CSV取り込み時に価格ルールが自動登録される機能をテストします。
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.import_service import ImportService
from app.models.customer_company import CustomerCompany
from app.models.product import Product
from app.models.pricing_rule import PricingRule


class TestPricingAutoRegister:
    """価格ルール自動登録機能のテスト"""

    def test_auto_register_new_rule(self, db_session: Session, test_customer: CustomerCompany):
        """
        新規価格ルールの自動登録テスト

        シナリオ:
        - CSVから「ハードケース」の単価 ¥800 を取り込む
        - 自動的に価格ルールが新規作成される
        - 次回インポート時にこの価格が適用される
        """
        # Arrange: テストデータ準備
        product_type_keyword = "ハードケース"
        csv_unit_price = Decimal("800")

        # Act: 価格ルール自動登録を実行
        result = ImportService._auto_register_product_type_pricing(
            db=db_session,
            customer_id=test_customer.id,
            product_type_keyword=product_type_keyword,
            csv_unit_price=csv_unit_price
        )

        # Assert: 結果を検証
        assert result is not None, "メッセージが返されるべき"
        assert "新規登録" in result, "新規登録メッセージが含まれるべき"
        assert product_type_keyword in result
        assert "¥800" in result

        # データベースを確認
        rule = db_session.query(PricingRule).filter(
            PricingRule.customer_id == test_customer.id,
            PricingRule.product_type_keyword == product_type_keyword
        ).first()

        assert rule is not None, "価格ルールが作成されているべき"
        assert rule.price == csv_unit_price, "単価が正しく設定されているべき"
        assert rule.priority == 0, "優先度がデフォルト値であるべき"

    def test_auto_register_update_existing_rule(self, db_session: Session, test_customer: CustomerCompany):
        """
        既存価格ルールの自動更新テスト

        シナリオ:
        - 既に「ハードケース」の価格ルールが存在（¥800）
        - CSVから新しい単価 ¥850 を取り込む
        - 既存の価格ルールが自動更新される
        """
        # Arrange: 既存の価格ルールを作成
        product_type_keyword = "ハードケース"
        old_price = Decimal("800")
        new_price = Decimal("850")

        existing_rule = PricingRule(
            customer_id=test_customer.id,
            product_type_keyword=product_type_keyword,
            price=old_price,
            priority=0
        )
        db_session.add(existing_rule)
        db_session.commit()

        # Act: 新しい単価で価格ルール自動登録を実行
        result = ImportService._auto_register_product_type_pricing(
            db=db_session,
            customer_id=test_customer.id,
            product_type_keyword=product_type_keyword,
            csv_unit_price=new_price
        )

        # Assert: 結果を検証
        assert result is not None, "更新メッセージが返されるべき"
        assert "更新" in result, "更新メッセージが含まれるべき"
        assert "¥800 → ¥850" in result, "価格変更が表示されるべき"

        # データベースを確認
        rule = db_session.query(PricingRule).filter(
            PricingRule.customer_id == test_customer.id,
            PricingRule.product_type_keyword == product_type_keyword
        ).first()

        assert rule is not None
        assert rule.price == new_price, "単価が更新されているべき"

    def test_auto_register_skip_same_price(self, db_session: Session, test_customer: CustomerCompany):
        """
        同じ単価の場合はスキップするテスト

        シナリオ:
        - 既に「ハードケース」の価格ルールが存在（¥800）
        - CSVから同じ単価 ¥800 を取り込む
        - 更新はスキップされる（メッセージなし）
        """
        # Arrange: 既存の価格ルールを作成
        product_type_keyword = "ハードケース"
        same_price = Decimal("800")

        existing_rule = PricingRule(
            customer_id=test_customer.id,
            product_type_keyword=product_type_keyword,
            price=same_price,
            priority=0
        )
        db_session.add(existing_rule)
        db_session.commit()

        # Act: 同じ単価で価格ルール自動登録を実行
        result = ImportService._auto_register_product_type_pricing(
            db=db_session,
            customer_id=test_customer.id,
            product_type_keyword=product_type_keyword,
            csv_unit_price=same_price
        )

        # Assert: メッセージがNoneであることを確認
        assert result is None, "同じ単価の場合はメッセージなし"

    def test_extract_product_keywords_hard_case(self):
        """
        商品キーワード抽出テスト: ハードケース

        デザイン名を除外し、商品タイプのみ抽出することを確認
        """
        product_name = "ハードケース(ボタニカル 青黄花柄：ホワイト)h077@04/F-53E_大(974)"
        keywords = ImportService._extract_product_keywords(product_name)

        assert keywords == "ハードケース", "商品タイプのみ抽出されるべき"

    def test_extract_product_keywords_flip_case_mirror(self):
        """
        商品キーワード抽出テスト: 手帳型カバー + mirror

        商品タイプとバリエーション（mirror）を抽出
        """
        product_name = "手帳型カバーmirror(刺繍風プリント：グリーン)095@04m/wish4(mirror)_3L(976)"
        keywords = ImportService._extract_product_keywords(product_name)

        assert keywords == "手帳型カバー / mirror", "商品タイプとmirrorが抽出されるべき"

    def test_extract_product_keywords_soft_case(self):
        """商品キーワード抽出テスト: ソフトケース"""
        product_name = "ソフトケース(花柄デザイン)"
        keywords = ImportService._extract_product_keywords(product_name)

        assert keywords == "ソフトケース"

    def test_extract_product_keywords_unknown(self):
        """商品キーワード抽出テスト: 未知の商品タイプ"""
        product_name = "不明な商品名"
        keywords = ImportService._extract_product_keywords(product_name)

        assert keywords == "", "未知の商品タイプは空文字列"

    def test_get_customer_price_with_product_type(
        self,
        db_session: Session,
        test_customer: CustomerCompany,
        test_product_hard_case: Product
    ):
        """
        商品タイプキーワードによる単価取得テスト

        シナリオ:
        - 「ハードケース」の価格ルールが存在（¥750）
        - 商品の標準単価は ¥1000
        - 価格ルールの単価（¥750）が優先される
        """
        # Arrange: 価格ルールを作成
        product_type_keyword = "ハードケース"
        special_price = Decimal("750")

        rule = PricingRule(
            customer_id=test_customer.id,
            product_type_keyword=product_type_keyword,
            price=special_price,
            priority=0
        )
        db_session.add(rule)
        db_session.commit()

        # Act: 単価を取得
        price = ImportService._get_customer_price(
            db=db_session,
            customer_id=test_customer.id,
            product_id=test_product_hard_case.id,
            quantity=1,
            default_price=test_product_hard_case.default_price,
            product_type_keyword=product_type_keyword
        )

        # Assert: 価格ルールの単価が返される
        assert price == special_price, "価格ルールの単価が優先されるべき"

    def test_get_customer_price_fallback_to_default(
        self,
        db_session: Session,
        test_customer: CustomerCompany,
        test_product_hard_case: Product
    ):
        """
        デフォルト単価へのフォールバックテスト

        シナリオ:
        - 価格ルールが存在しない
        - 商品の標準単価（¥1000）が使用される
        """
        # Act: 単価を取得（商品タイプキーワードなし）
        price = ImportService._get_customer_price(
            db=db_session,
            customer_id=test_customer.id,
            product_id=test_product_hard_case.id,
            quantity=1,
            default_price=test_product_hard_case.default_price,
            product_type_keyword=None
        )

        # Assert: 商品の標準単価が返される
        assert price == test_product_hard_case.default_price, "標準単価が使用されるべき"


@pytest.mark.integration
class TestPricingAutoRegisterIntegration:
    """統合テスト: 実際のインポート処理での動作確認"""

    def test_import_with_auto_pricing_registration(
        self,
        db_session: Session,
        test_issuer,
        test_customer: CustomerCompany,
        test_product_hard_case: Product
    ):
        """
        統合テスト: CSV取り込み時の価格ルール自動登録

        シナリオ:
        1. CSVデータを取り込む（商品タイプ: ハードケース、単価: ¥800）
        2. 注文が作成される
        3. 価格ルールが自動登録される
        4. 次回インポート時、登録された単価が適用される
        """
        # Arrange: CSVデータ
        csv_data = [
            {
                'customer_name': test_customer.name,
                'product_name': test_product_hard_case.name,
                'extracted_memo': 'ハードケース',
                'quantity': '10',
                'unit_price': '800'
            }
        ]

        # Act: インポート実行
        result = ImportService.import_order_data(
            db=db_session,
            data=csv_data,
            use_ai_classification=False,
            issuer_id=test_issuer.id,
            customer_id=test_customer.id
        )

        # Assert: インポート成功
        assert result['success'] is True, "インポートが成功するべき"
        assert result['imported_rows'] == 1, "1件インポートされるべき"

        # 価格ルールが作成されたか確認
        rule = db_session.query(PricingRule).filter(
            PricingRule.customer_id == test_customer.id,
            PricingRule.product_type_keyword == 'ハードケース'
        ).first()

        assert rule is not None, "価格ルールが作成されているべき"
        assert rule.price == Decimal("800"), "CSVの単価が登録されているべき"

        # 警告メッセージに価格ルール登録が含まれるか確認
        warnings = result.get('warnings', [])
        pricing_warning = [w for w in warnings if '価格ルール' in w]
        assert len(pricing_warning) > 0, "価格ルール登録の警告があるべき"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
