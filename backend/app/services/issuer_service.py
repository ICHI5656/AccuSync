"""
Issuer Company service for managing default issuer company.
"""

import os
from typing import Optional
from sqlalchemy.orm import Session

from app.models.issuer_company import IssuerCompany


class IssuerService:
    """
    Service for managing issuer companies (請求者会社).
    """

    @staticmethod
    def get_or_create_default_issuer(db: Session) -> IssuerCompany:
        """
        デフォルトの請求者会社を取得または作成します。

        環境変数から請求者情報を読み取り、存在しない場合は作成します。
        既存の請求者がある場合は最初の1件を返します。

        Args:
            db: データベースセッション

        Returns:
            IssuerCompany: デフォルトの請求者会社
        """
        # 既存の請求者を検索（最初の1件を返す）
        existing_issuer = db.query(IssuerCompany).first()

        if existing_issuer:
            return existing_issuer

        # 環境変数から請求者情報を取得
        default_name = os.getenv('DEFAULT_ISSUER_NAME', '株式会社AccuSync')
        default_brand = os.getenv('DEFAULT_ISSUER_BRAND', None)
        default_tax_id = os.getenv('DEFAULT_ISSUER_TAX_ID', None)
        default_address = os.getenv('DEFAULT_ISSUER_ADDRESS', '東京都渋谷区')
        default_tel = os.getenv('DEFAULT_ISSUER_TEL', '03-0000-0000')
        default_email = os.getenv('DEFAULT_ISSUER_EMAIL', 'info@accusync.example.com')

        # 新規請求者を作成
        new_issuer = IssuerCompany(
            name=default_name,
            brand_name=default_brand,
            tax_id=default_tax_id,
            address=default_address,
            tel=default_tel,
            email=default_email,
            bank_info=None,
            logo_url=None,
            seal_url=None,
            invoice_notes='お支払いは請求書記載の期日までにお願いいたします。'
        )

        db.add(new_issuer)
        db.flush()

        return new_issuer

    @staticmethod
    def get_default_issuer(db: Session) -> Optional[IssuerCompany]:
        """
        デフォルトの請求者会社を取得します（作成しない）。

        Args:
            db: データベースセッション

        Returns:
            Optional[IssuerCompany]: 請求者会社、存在しない場合はNone
        """
        return db.query(IssuerCompany).first()

    @staticmethod
    def get_or_create_issuer_by_name(
        db: Session,
        name: str,
        **kwargs
    ) -> IssuerCompany:
        """
        名前で請求者会社を検索し、存在しない場合は作成します。

        Args:
            db: データベースセッション
            name: 請求者会社名
            **kwargs: その他のフィールド（address, tel, emailなど）

        Returns:
            IssuerCompany: 請求者会社
        """
        # 名前で検索
        issuer = db.query(IssuerCompany).filter(
            IssuerCompany.name == name
        ).first()

        if issuer:
            return issuer

        # 新規作成
        issuer = IssuerCompany(
            name=name,
            brand_name=kwargs.get('brand_name'),
            tax_id=kwargs.get('tax_id'),
            address=kwargs.get('address'),
            tel=kwargs.get('tel'),
            email=kwargs.get('email'),
            bank_info=kwargs.get('bank_info'),
            logo_url=kwargs.get('logo_url'),
            seal_url=kwargs.get('seal_url'),
            invoice_notes=kwargs.get('invoice_notes', 'お支払いは請求書記載の期日までにお願いいたします。')
        )

        db.add(issuer)
        db.flush()

        return issuer
