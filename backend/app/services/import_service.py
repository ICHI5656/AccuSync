"""
Import service for saving parsed data to database.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import asyncio

from app.models.order import Order, OrderItem
from app.models.customer_company import CustomerCompany
from app.models.product import Product
from app.ai.factory import AIProviderFactory
from app.services.issuer_service import IssuerService


class ImportService:
    """
    Service for importing parsed data into database.
    """

    @staticmethod
    def _get_field_value(row: Dict[str, Any], standard_key: str, fallback_keys: List[str]) -> Any:
        """
        Get field value from row, trying standard key first, then fallback keys.

        Args:
            row: Data row
            standard_key: Standard field key (e.g., 'customer_name')
            fallback_keys: List of fallback keys to try (e.g., ['顧客名', '受注先名'])

        Returns:
            Field value or None
        """
        # Try standard key first
        value = row.get(standard_key)
        if value:
            return value

        # Try fallback keys
        for key in fallback_keys:
            value = row.get(key)
            if value:
                return value

        return None

    @staticmethod
    def import_order_data(
        db: Session,
        data: List[Dict[str, Any]],
        column_mapping: Optional[Dict[str, str]] = None,
        use_ai_classification: bool = True,
        issuer_id: Optional[int] = None,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import order data into database.

        Args:
            db: Database session
            data: Parsed data rows
            column_mapping: Optional column name mapping
            use_ai_classification: Whether to use AI for customer classification
            issuer_id: Optional issuer company ID (defaults to first issuer)
            customer_id: Optional customer company ID (if specified, use existing customer)

        Returns:
            Import results summary
        """
        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        warnings = []

        # 請求者を取得（指定されたIDまたはデフォルト）
        try:
            if issuer_id:
                from app.models.issuer_company import IssuerCompany
                default_issuer = db.query(IssuerCompany).filter(IssuerCompany.id == issuer_id).first()
                if not default_issuer:
                    errors.append(f'指定された請求者会社（ID: {issuer_id}）が見つかりません')
                    return {
                        'success': False,
                        'imported_rows': 0,
                        'skipped_rows': 0,
                        'error_rows': 0,
                        'warnings': warnings,
                        'errors': errors
                    }
                warnings.append(f'請求者会社: {default_issuer.name} (ID: {default_issuer.id}) - 指定')
            else:
                default_issuer = IssuerService.get_or_create_default_issuer(db)
                warnings.append(f'請求者会社: {default_issuer.name} (ID: {default_issuer.id}) - デフォルト')
        except Exception as e:
            errors.append(f'請求者会社の取得に失敗: {str(e)}')
            return {
                'success': False,
                'imported_rows': 0,
                'skipped_rows': 0,
                'error_rows': 0,
                'warnings': warnings,
                'errors': errors
            }

        # 顧客会社が指定されている場合は取得
        specified_customer = None
        if customer_id:
            specified_customer = db.query(CustomerCompany).filter(
                CustomerCompany.id == customer_id
            ).first()
            if not specified_customer:
                errors.append(f'指定された取引先会社（ID: {customer_id}）が見つかりません')
                return {
                    'success': False,
                    'imported_rows': 0,
                    'skipped_rows': 0,
                    'error_rows': 0,
                    'warnings': warnings,
                    'errors': errors
                }
            warnings.append(f'取引先会社: {specified_customer.name} (ID: {specified_customer.id}) - すべてのデータをこの会社に紐付けます')

        for row_index, row in enumerate(data, 1):
            try:
                # Apply column mapping if provided
                if column_mapping:
                    mapped_row = {}
                    for target_field, source_column in column_mapping.items():
                        if source_column in row:
                            mapped_row[target_field] = row[source_column]
                    row = mapped_row

                # 顧客会社の決定
                if specified_customer:
                    # 指定された顧客会社を使用
                    customer = specified_customer
                else:
                    # 従来通り、顧客名から検索または新規作成
                    # Extract order information using standard fields
                    customer_name = ImportService._get_field_value(
                        row, 'customer_name', ['顧客名', '受注先名', 'お客様名', '取引先名', '会社名', '氏名']
                    )
                    if not customer_name:
                        warnings.append(f'Row {row_index}: 顧客名が見つかりません')
                        skipped_count += 1
                        continue

                    # Find or create customer
                    customer = db.query(CustomerCompany).filter(
                        CustomerCompany.name == customer_name
                    ).first()

                    if not customer:
                        # AI判定で会社か個人かを判定
                        is_individual = False
                        if use_ai_classification:
                            try:
                                ai_provider = AIProviderFactory.create()
                                additional_info = {
                                    'address': ImportService._get_field_value(row, 'address', ['住所', '所在地']),
                                    'phone': ImportService._get_field_value(row, 'phone', ['電話番号', '電話', 'TEL', 'tel']),
                                    'email': ImportService._get_field_value(row, 'email', ['メールアドレス', 'メール', 'Eメール'])
                                }
                                # asyncio.run()を使用してasync関数を呼び出し
                                classification_result = asyncio.run(
                                    ai_provider.classify_customer_type(
                                        customer_name=customer_name,
                                        additional_info=additional_info
                                    )
                                )
                                is_individual = classification_result.is_individual
                                if classification_result.confidence >= 0.7:
                                    customer_type = "個人" if is_individual else "法人"
                                    warnings.append(
                                        f'Row {row_index}: AI判定 - {customer_name}は{customer_type} '
                                        f'(信頼度: {classification_result.confidence:.2f}, '
                                        f'理由: {classification_result.reason})'
                                    )
                            except Exception as e:
                                warnings.append(f'Row {row_index}: AI判定失敗 - {str(e)}')

                        # Create new customer
                        customer_code = f"CUST{datetime.now().strftime('%Y%m%d%H%M%S')}{row_index}"
                        customer = CustomerCompany(
                            code=customer_code,
                            name=customer_name,
                            is_individual=is_individual,
                            address=ImportService._get_field_value(row, 'address', ['住所', '所在地']),
                            postal_code=ImportService._get_field_value(row, 'postal_code', ['郵便番号', '〒']),
                            phone=ImportService._get_field_value(row, 'phone', ['電話番号', '電話', 'TEL', 'tel']),
                            email=ImportService._get_field_value(row, 'email', ['メールアドレス', 'メール', 'Eメール'])
                        )
                        db.add(customer)
                        db.flush()
                        customer_type = "個人" if is_individual else "法人"
                        warnings.append(f'Row {row_index}: 新規顧客({customer_type})を作成しました - {customer_name}')

                # Extract product information
                product_name = ImportService._get_field_value(
                    row, 'product_name', ['商品名', '品名', '製品名', '機種', 'アイテム名']
                )
                if not product_name:
                    warnings.append(f'Row {row_index}: 商品名が見つかりません')
                    skipped_count += 1
                    continue

                # Extract product SKU (optional)
                product_sku_value = ImportService._get_field_value(
                    row, 'product_sku', ['商品コード', '品番', 'SKU', 'コード']
                )

                # Extract order details (needed for product creation)
                quantity_value = ImportService._get_field_value(row, 'quantity', ['数量', '個数', '数', 'qty'])
                quantity = int(ImportService._parse_number(quantity_value or '1'))

                unit_price_value = ImportService._get_field_value(row, 'unit_price', ['単価', '価格', '金額'])
                unit_price = Decimal(str(ImportService._parse_number(unit_price_value or '0')))

                # Find or create product
                product = None

                # Search by SKU first if provided
                if product_sku_value:
                    product = db.query(Product).filter(
                        Product.sku == product_sku_value
                    ).first()

                # If not found by SKU, search by name
                if not product:
                    product = db.query(Product).filter(
                        Product.name == product_name
                    ).first()

                if not product:
                    # 商品が見つからない場合はスキップ
                    warnings.append(f'Row {row_index}: 商品 "{product_name}" が商品マスタに登録されていません - スキップしました')
                    skipped_count += 1
                    continue

                # Create order
                order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{row_index}"
                memo_value = ImportService._get_field_value(row, 'notes', ['備考', 'メモ', '注記', 'コメント'])
                order = Order(
                    customer_id=customer.id,
                    issuer_company_id=default_issuer.id,  # デフォルト請求者を設定
                    source='csv',
                    order_no=order_no,
                    order_date=datetime.now().date(),
                    memo=memo_value or ''
                )
                db.add(order)
                db.flush()

                # Create order item
                subtotal = Decimal(quantity) * unit_price
                tax_rate_decimal = Decimal(str(product.tax_rate))
                tax_amount = subtotal * tax_rate_decimal
                total = subtotal + tax_amount

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    qty=quantity,
                    unit_price=unit_price,
                    subtotal_ex_tax=subtotal,
                    tax_rate=tax_rate_decimal,
                    tax_amount=tax_amount,
                    total_in_tax=total
                )
                db.add(order_item)

                imported_count += 1

            except IntegrityError as e:
                db.rollback()
                error_count += 1
                errors.append(f'Row {row_index}: データベースエラー - {str(e)}')
            except Exception as e:
                error_count += 1
                errors.append(f'Row {row_index}: {str(e)}')

        # Commit all changes
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            errors.append(f'コミットエラー: {str(e)}')
            return {
                'success': False,
                'imported_rows': 0,
                'skipped_rows': len(data),
                'error_rows': len(data),
                'errors': errors,
                'warnings': warnings
            }

        return {
            'success': imported_count > 0,
            'imported_rows': imported_count,
            'skipped_rows': skipped_count,
            'error_rows': error_count,
            'errors': errors,
            'warnings': warnings
        }

    @staticmethod
    def _parse_number(value: Any) -> float:
        """Parse number from various formats."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove common formatting
            cleaned = value.replace(',', '').replace('¥', '').replace('円', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0
