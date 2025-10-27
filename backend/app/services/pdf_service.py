"""PDF Generation Service - 請求書・納品書PDF生成"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import re

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader, Template

from app.core.config import settings


class PDFService:
    """PDF生成サービス

    HTMLテンプレートを使用して請求書・納品書PDFを生成します
    """

    def __init__(self):
        """初期化"""
        self.template_dir = Path(__file__).parent.parent.parent.parent / "templates"

        # Jinja2環境のセットアップ
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # カスタムフィルター登録
        self.jinja_env.filters['format_currency'] = self._format_currency
        self.jinja_env.filters['format_date'] = self._format_date

    def _format_currency(self, value: float) -> str:
        """金額をフォーマット

        Args:
            value: 金額

        Returns:
            フォーマットされた金額（例: 1,234,567）
        """
        return f"{int(value):,}"

    def _format_date(self, value: Any, format: str = "%Y年%m月%d日") -> str:
        """日付をフォーマット

        Args:
            value: 日付（datetime, date, または文字列）
            format: フォーマット文字列

        Returns:
            フォーマットされた日付
        """
        if isinstance(value, str):
            # ISO形式の文字列をパース
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))

        if hasattr(value, 'strftime'):
            return value.strftime(format)

        return str(value)

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """テンプレートをレンダリング

        Handlebars風のプレースホルダーをJinja2形式に変換してレンダリング

        Args:
            template_name: テンプレートファイル名
            context: テンプレート変数

        Returns:
            レンダリングされたHTML
        """
        # テンプレートファイルを読み込み
        template_path = self.template_dir / template_name
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Handlebars風の構文をJinja2に変換
        # {variable} → {{ variable }}
        template_content = re.sub(r'\{([a-zA-Z_][\w.]*)\}', r'{{ \1 }}', template_content)

        # {#each items} → {% for item in items %}
        template_content = re.sub(r'\{#each\s+(\w+)\}', r'{% for item in \1 %}', template_content)

        # {/each} → {% endfor %}
        template_content = re.sub(r'\{/each\}', r'{% endfor %}', template_content)

        # Jinja2テンプレートとしてレンダリング
        template = Template(template_content)
        return template.render(**context)

    def generate_invoice_pdf(
        self,
        invoice_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """請求書PDFを生成

        Args:
            invoice_data: 請求書データ
                - invoice_no: 請求書番号
                - issue_date: 発行日
                - due_date: 支払期限
                - period_start: 期間開始日
                - period_end: 期間終了日
                - issuer: 発行元情報（name, tax_id, address, tel, email, bank_info）
                - customer: 顧客情報（name, person, address, email）
                - items: 明細リスト（description, qty, unit, unit_price, subtotal_ex_tax, tax_rate）
                - subtotal_ex_tax: 税抜小計
                - tax_amount: 消費税額
                - total_in_tax: 税込合計
                - payment_terms: 支払条件
                - notes: 備考
            output_path: 出力ファイルパス（オプション）

        Returns:
            PDFバイト列
        """
        # テンプレートコンテキストを準備
        context = {
            **invoice_data,
            # 金額フォーマット
            'subtotal_ex_tax': self._format_currency(invoice_data.get('subtotal_ex_tax', 0)),
            'tax_amount': self._format_currency(invoice_data.get('tax_amount', 0)),
            'total_in_tax': self._format_currency(invoice_data.get('total_in_tax', 0)),
            # 日付フォーマット
            'issue_date': self._format_date(invoice_data.get('issue_date', datetime.now())),
            'due_date': self._format_date(invoice_data.get('due_date', datetime.now())),
            'period_start': self._format_date(invoice_data.get('period_start', datetime.now())),
            'period_end': self._format_date(invoice_data.get('period_end', datetime.now())),
        }

        # 明細データもフォーマット
        if 'items' in context:
            formatted_items = []
            for item in context['items']:
                formatted_item = {
                    **item,
                    'unit_price': self._format_currency(item.get('unit_price', 0)),
                    'subtotal_ex_tax': self._format_currency(item.get('subtotal_ex_tax', 0)),
                    'tax_rate': int(item.get('tax_rate', 0.1) * 100),  # 0.1 → 10
                }
                formatted_items.append(formatted_item)
            context['items'] = formatted_items

        # HTMLをレンダリング
        html_content = self._render_template('invoice.html', context)

        # PDFを生成
        pdf_bytes = HTML(string=html_content, base_url=str(self.template_dir)).write_pdf()

        # ファイルに保存（オプション）
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    def generate_delivery_note_pdf(
        self,
        delivery_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """納品書PDFを生成

        Args:
            delivery_data: 納品書データ
                - slip_no: 伝票番号
                - issue_date: 発行日
                - ship_date: 出荷日
                - issuer: 発行元情報（name, address, tel, person）
                - customer: 顧客情報（name, person）
                - delivery: 配送先情報（address, tel）
                - items: 明細リスト（description, qty, unit, memo）
                - payment_terms: 支払条件
            output_path: 出力ファイルパス（オプション）

        Returns:
            PDFバイト列
        """
        # テンプレートコンテキストを準備
        context = {
            **delivery_data,
            # 日付フォーマット
            'issue_date': self._format_date(delivery_data.get('issue_date', datetime.now())),
            'ship_date': self._format_date(delivery_data.get('ship_date', datetime.now())),
        }

        # HTMLをレンダリング
        html_content = self._render_template('delivery_note.html', context)

        # PDFを生成
        pdf_bytes = HTML(string=html_content, base_url=str(self.template_dir)).write_pdf()

        # ファイルに保存（オプション）
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes
