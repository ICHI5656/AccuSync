"""
Auto Invoice Service - 自動請求書発行サービス

締め日に基づいて自動的に請求書を生成します。
"""

from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
import calendar
import logging

from app.models.customer_company import CustomerCompany
from app.models.order import Order
from app.services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)


class AutoInvoiceService:
    """自動請求書発行サービス

    顧客の締め日をチェックして、自動的に請求書を生成します。
    """

    @staticmethod
    def get_last_day_of_month(year: int, month: int) -> int:
        """月末日を取得

        Args:
            year: 年
            month: 月

        Returns:
            その月の最終日（28-31）
        """
        return calendar.monthrange(year, month)[1]

    @staticmethod
    def normalize_closing_day(closing_day: int, year: int, month: int) -> int:
        """締め日を正規化

        Args:
            closing_day: 締め日（0=月末、1-31=指定日）
            year: 年
            month: 月

        Returns:
            実際の日（1-31）
        """
        if closing_day == 0:
            # 0 = 月末
            return AutoInvoiceService.get_last_day_of_month(year, month)

        # 指定日が月の日数を超える場合は月末にする
        last_day = AutoInvoiceService.get_last_day_of_month(year, month)
        return min(closing_day, last_day)

    @staticmethod
    def get_customers_to_invoice(db: Session, target_date: date = None) -> List[CustomerCompany]:
        """請求書を発行すべき顧客を取得

        Args:
            db: データベースセッション
            target_date: チェック対象日（Noneの場合は今日）

        Returns:
            請求書を発行すべき顧客のリスト
        """
        if target_date is None:
            target_date = datetime.now().date()

        # 締め日が設定されている顧客を取得
        customers = db.query(CustomerCompany).filter(
            CustomerCompany.closing_day.isnot(None)
        ).all()

        customers_to_invoice = []

        for customer in customers:
            # 今月の正規化された締め日を取得
            normalized_closing_day = AutoInvoiceService.normalize_closing_day(
                customer.closing_day,
                target_date.year,
                target_date.month
            )

            # 今日が締め日かチェック
            if target_date.day == normalized_closing_day:
                customers_to_invoice.append(customer)
                logger.info(
                    f"Customer {customer.name} (ID: {customer.id}) "
                    f"has closing day today: {normalized_closing_day}"
                )

        return customers_to_invoice

    @staticmethod
    def calculate_invoice_period(
        customer: CustomerCompany,
        closing_date: date
    ) -> tuple[date, date]:
        """請求期間を計算

        Args:
            customer: 顧客
            closing_date: 締め日

        Returns:
            (period_start, period_end) のタプル
        """
        # 期間終了日 = 締め日
        period_end = closing_date

        # 期間開始日 = 前回の締め日の翌日
        # 前月の同じ締め日を計算
        prev_month = closing_date.month - 1 if closing_date.month > 1 else 12
        prev_year = closing_date.year if closing_date.month > 1 else closing_date.year - 1

        # 前月の締め日を正規化
        prev_closing_day = AutoInvoiceService.normalize_closing_day(
            customer.closing_day,
            prev_year,
            prev_month
        )

        # 前回締め日の翌日
        try:
            period_start = date(prev_year, prev_month, prev_closing_day) + timedelta(days=1)
        except ValueError:
            # 日付が無効な場合は月初から
            period_start = date(closing_date.year, closing_date.month, 1)

        return period_start, period_end

    @staticmethod
    def calculate_payment_due_date(
        customer: CustomerCompany,
        closing_date: date
    ) -> date:
        """支払期限を計算

        Args:
            customer: 顧客
            closing_date: 締め日

        Returns:
            支払期限日
        """
        # payment_month_offset: 0=当月、1=翌月、2=翌々月
        month_offset = customer.payment_month_offset or 1
        payment_day = customer.payment_day or 0

        # オフセット後の年月を計算
        target_month = closing_date.month + month_offset
        target_year = closing_date.year

        while target_month > 12:
            target_month -= 12
            target_year += 1

        # 支払日を正規化
        normalized_payment_day = AutoInvoiceService.normalize_closing_day(
            payment_day,
            target_year,
            target_month
        )

        try:
            due_date = date(target_year, target_month, normalized_payment_day)
        except ValueError:
            # 無効な日付の場合は月末
            last_day = AutoInvoiceService.get_last_day_of_month(target_year, target_month)
            due_date = date(target_year, target_month, last_day)

        return due_date

    @staticmethod
    def auto_generate_invoice_for_customer(
        db: Session,
        customer: CustomerCompany,
        closing_date: date = None
    ) -> Dict[str, Any]:
        """顧客の請求書を自動生成

        Args:
            db: データベースセッション
            customer: 顧客
            closing_date: 締め日（Noneの場合は今日）

        Returns:
            生成結果の辞書
        """
        if closing_date is None:
            closing_date = datetime.now().date()

        try:
            # 請求期間を計算
            period_start, period_end = AutoInvoiceService.calculate_invoice_period(
                customer, closing_date
            )

            logger.info(
                f"Generating invoice for {customer.name} "
                f"(period: {period_start} - {period_end})"
            )

            # 期間内の注文があるかチェック
            order_count = db.query(Order).filter(
                and_(
                    Order.customer_id == customer.id,
                    Order.order_date >= period_start,
                    Order.order_date <= period_end
                )
            ).count()

            if order_count == 0:
                logger.info(
                    f"No orders found for {customer.name} in period "
                    f"{period_start} - {period_end}, skipping invoice generation"
                )
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'no_orders',
                    'customer_id': customer.id,
                    'customer_name': customer.name,
                    'period_start': period_start,
                    'period_end': period_end,
                    'order_count': 0
                }

            # 請求書を生成
            invoice = InvoiceService.create_invoice(
                db=db,
                customer_id=customer.id,
                period_start=period_start,
                period_end=period_end,
                notes=f"自動生成（締め日: {closing_date}）"
            )

            logger.info(
                f"Successfully generated invoice {invoice.invoice_no} "
                f"for {customer.name} (ID: {invoice.id})"
            )

            return {
                'success': True,
                'skipped': False,
                'invoice_id': invoice.id,
                'invoice_no': invoice.invoice_no,
                'customer_id': customer.id,
                'customer_name': customer.name,
                'period_start': period_start,
                'period_end': period_end,
                'order_count': order_count,
                'total_amount': float(invoice.total_in_tax)
            }

        except ValueError as e:
            logger.error(f"Error generating invoice for {customer.name}: {str(e)}")
            return {
                'success': False,
                'skipped': False,
                'error': str(e),
                'customer_id': customer.id,
                'customer_name': customer.name
            }
        except Exception as e:
            logger.error(
                f"Unexpected error generating invoice for {customer.name}: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'skipped': False,
                'error': f"Unexpected error: {str(e)}",
                'customer_id': customer.id,
                'customer_name': customer.name
            }

    @staticmethod
    def run_auto_invoice_generation(
        db: Session,
        target_date: date = None
    ) -> Dict[str, Any]:
        """自動請求書生成を実行

        Args:
            db: データベースセッション
            target_date: チェック対象日（Noneの場合は今日）

        Returns:
            実行結果の辞書
        """
        if target_date is None:
            target_date = datetime.now().date()

        logger.info(f"Starting auto invoice generation for date: {target_date}")

        # 請求書を発行すべき顧客を取得
        customers = AutoInvoiceService.get_customers_to_invoice(db, target_date)

        if not customers:
            logger.info("No customers with closing day today")
            return {
                'success': True,
                'date': target_date,
                'customers_checked': 0,
                'invoices_generated': 0,
                'invoices_skipped': 0,
                'errors': 0,
                'results': []
            }

        logger.info(f"Found {len(customers)} customers with closing day today")

        # 各顧客の請求書を生成
        results = []
        invoices_generated = 0
        invoices_skipped = 0
        errors = 0

        for customer in customers:
            result = AutoInvoiceService.auto_generate_invoice_for_customer(
                db, customer, target_date
            )
            results.append(result)

            if result['success']:
                if result.get('skipped'):
                    invoices_skipped += 1
                else:
                    invoices_generated += 1
            else:
                errors += 1

        summary = {
            'success': True,
            'date': target_date,
            'customers_checked': len(customers),
            'invoices_generated': invoices_generated,
            'invoices_skipped': invoices_skipped,
            'errors': errors,
            'results': results
        }

        logger.info(
            f"Auto invoice generation completed: "
            f"{invoices_generated} generated, {invoices_skipped} skipped, {errors} errors"
        )

        return summary
