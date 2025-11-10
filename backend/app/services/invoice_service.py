"""
Invoice Service - 請求書生成・管理サービス
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.invoice import Invoice, InvoiceItem
from app.models.order import Order, OrderItem
from app.models.customer_company import CustomerCompany
from app.models.issuer_company import IssuerCompany
from app.models.product import Product


class InvoiceService:
    """請求書サービス

    受注データから請求書を生成・管理します。
    """

    @staticmethod
    def generate_invoice_number(issue_date: date) -> str:
        """請求書番号を生成

        Args:
            issue_date: 発行日

        Returns:
            請求書番号（例: INV-20251029-001）
        """
        date_str = issue_date.strftime("%Y%m%d")
        # 本来はDBで採番すべきだが、簡易的にタイムスタンプを使用
        timestamp = datetime.now().strftime("%H%M%S")
        return f"INV-{date_str}-{timestamp}"

    @staticmethod
    def aggregate_orders_for_invoice(
        db: Session,
        customer_id: int,
        period_start: date,
        period_end: date,
        issuer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """指定期間の注文を集計して請求書データを作成

        Args:
            db: データベースセッション
            customer_id: 取引先ID
            period_start: 集計期間開始日
            period_end: 集計期間終了日
            issuer_id: 発行会社ID（任意）

        Returns:
            集計された請求書データ
        """
        # 顧客情報を取得
        customer = db.query(CustomerCompany).filter(
            CustomerCompany.id == customer_id
        ).first()

        if not customer:
            raise ValueError(f"顧客ID {customer_id} が見つかりません")

        # 発行会社を取得
        if issuer_id:
            issuer = db.query(IssuerCompany).filter(
                IssuerCompany.id == issuer_id
            ).first()
        else:
            # デフォルト発行会社を使用
            from app.services.issuer_service import IssuerService
            issuer = IssuerService.get_or_create_default_issuer(db)

        # 期間内の注文を取得
        orders = db.query(Order).filter(
            Order.customer_id == customer_id,
            Order.order_date >= period_start,
            Order.order_date <= period_end
        ).all()

        if not orders:
            return {
                'success': False,
                'error': f'指定期間（{period_start} 〜 {period_end}）に注文が見つかりません',
                'order_count': 0
            }

        # 注文明細を商品別に集計
        product_aggregates = {}

        for order in orders:
            for item in order.items:
                product_key = item.product_id or item.product.name if item.product else "不明な商品"

                if product_key not in product_aggregates:
                    product_aggregates[product_key] = {
                        'product_id': item.product_id,
                        'product_name': item.product.name if item.product else "不明な商品",
                        'unit_price': item.unit_price,
                        'tax_rate': item.tax_rate,
                        'total_qty': 0,
                        'subtotal_ex_tax': Decimal('0'),
                        'tax_amount': Decimal('0'),
                        'total_in_tax': Decimal('0')
                    }

                agg = product_aggregates[product_key]
                agg['total_qty'] += item.qty
                agg['subtotal_ex_tax'] += item.subtotal_ex_tax
                agg['tax_amount'] += item.tax_amount
                agg['total_in_tax'] += item.total_in_tax

        # 請求書明細リストを作成
        invoice_items = []
        total_subtotal_ex_tax = Decimal('0')
        total_tax_amount = Decimal('0')
        total_in_tax = Decimal('0')

        for product_key, agg in product_aggregates.items():
            invoice_items.append({
                'product_id': agg['product_id'],
                'description': agg['product_name'],
                'qty': agg['total_qty'],
                'unit_price': agg['unit_price'],
                'tax_rate': agg['tax_rate'],
                'subtotal_ex_tax': agg['subtotal_ex_tax'],
                'tax_amount': agg['tax_amount'],
                'total_in_tax': agg['total_in_tax']
            })

            total_subtotal_ex_tax += agg['subtotal_ex_tax']
            total_tax_amount += agg['tax_amount']
            total_in_tax += agg['total_in_tax']

        # 支払期限を計算（発行日の翌月末）
        issue_date = datetime.now().date()
        if issue_date.month == 12:
            due_date = date(issue_date.year + 1, 1, 31)
        else:
            next_month = issue_date.month + 1
            # 月末日を取得
            import calendar
            last_day = calendar.monthrange(issue_date.year, next_month)[1]
            due_date = date(issue_date.year, next_month, last_day)

        return {
            'success': True,
            'order_count': len(orders),
            'invoice_data': {
                'issuer_company_id': issuer.id,
                'customer_id': customer.id,
                'period_start': period_start,
                'period_end': period_end,
                'issue_date': issue_date,
                'due_date': due_date,
                'subtotal_ex_tax': total_subtotal_ex_tax,
                'tax_amount': total_tax_amount,
                'total_in_tax': total_in_tax,
                'items': invoice_items
            }
        }

    @staticmethod
    def create_invoice(
        db: Session,
        customer_id: int,
        period_start: date,
        period_end: date,
        issuer_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Invoice:
        """請求書を作成

        Args:
            db: データベースセッション
            customer_id: 取引先ID
            period_start: 集計期間開始日
            period_end: 集計期間終了日
            issuer_id: 発行会社ID（任意）
            notes: 備考

        Returns:
            作成された請求書
        """
        # 注文を集計
        aggregation = InvoiceService.aggregate_orders_for_invoice(
            db=db,
            customer_id=customer_id,
            period_start=period_start,
            period_end=period_end,
            issuer_id=issuer_id
        )

        if not aggregation['success']:
            raise ValueError(aggregation['error'])

        invoice_data = aggregation['invoice_data']

        # 請求書番号を生成
        invoice_no = InvoiceService.generate_invoice_number(invoice_data['issue_date'])

        # 請求書ヘッダを作成
        invoice = Invoice(
            invoice_no=invoice_no,
            issuer_company_id=invoice_data['issuer_company_id'],
            customer_id=invoice_data['customer_id'],
            period_start=invoice_data['period_start'],
            period_end=invoice_data['period_end'],
            issue_date=invoice_data['issue_date'],
            due_date=invoice_data['due_date'],
            subtotal_ex_tax=invoice_data['subtotal_ex_tax'],
            tax_amount=invoice_data['tax_amount'],
            total_in_tax=invoice_data['total_in_tax'],
            status='draft',
            notes=notes
        )
        db.add(invoice)
        db.flush()

        # 請求書明細を作成
        for item_data in invoice_data['items']:
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item_data['product_id'],
                description=item_data['description'],
                qty=item_data['qty'],
                unit_price=item_data['unit_price'],
                tax_rate=item_data['tax_rate'],
                subtotal_ex_tax=item_data['subtotal_ex_tax'],
                tax_amount=item_data['tax_amount'],
                total_in_tax=item_data['total_in_tax']
            )
            db.add(invoice_item)

        db.commit()
        db.refresh(invoice)

        return invoice

    @staticmethod
    def get_invoice_preview_data(
        db: Session,
        invoice_id: int
    ) -> Dict[str, Any]:
        """請求書プレビュー用データを取得

        Args:
            db: データベースセッション
            invoice_id: 請求書ID

        Returns:
            PDFService用の請求書データ
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise ValueError(f"請求書ID {invoice_id} が見つかりません")

        # 発行会社情報
        issuer_data = {
            'name': invoice.issuer_company.name,
            'tax_id': invoice.issuer_company.tax_id or '',
            'address': invoice.issuer_company.address or '',
            'tel': invoice.issuer_company.tel or '',
            'email': invoice.issuer_company.email or '',
            'bank_info': invoice.issuer_company.bank_name or ''  # 振込先情報
        }

        # 顧客情報
        customer_data = {
            'name': invoice.customer.name,
            'person': '',  # 担当者名（現在未実装）
            'address': invoice.customer.address or '',
            'postal_code': invoice.customer.postal_code or '',
            'email': invoice.customer.email or ''
        }

        # 明細情報
        items_data = []
        for item in invoice.items:
            items_data.append({
                'description': item.description,
                'qty': item.qty,
                'unit': '個',  # TODO: 商品から取得
                'unit_price': float(item.unit_price),
                'subtotal_ex_tax': float(item.subtotal_ex_tax),
                'tax_rate': float(item.tax_rate)
            })

        return {
            'invoice_no': invoice.invoice_no,
            'issue_date': invoice.issue_date,
            'due_date': invoice.due_date,
            'period_start': invoice.period_start,
            'period_end': invoice.period_end,
            'issuer': issuer_data,
            'customer': customer_data,
            'items': items_data,
            'subtotal_ex_tax': float(invoice.subtotal_ex_tax),
            'tax_amount': float(invoice.tax_amount),
            'total_in_tax': float(invoice.total_in_tax),
            'notes': invoice.notes or ''
        }
