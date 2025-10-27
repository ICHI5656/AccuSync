# 02. データモデル（PostgreSQL）

ERD（簡略）:
```
IssuerCompany (id, name, brand_name, tax_id, address, tel, email, bank_info, logo_url, seal_url, invoice_notes, created_at, updated_at)
CustomerCompany (id, name, code, is_individual, postal_code, address, billing_address, phone, email, contact_name, contact_email, payment_terms, tax_mode, notes, created_at, updated_at)
Product (id, sku, name, default_price, tax_rate, tax_category, unit, is_active, created_at, updated_at)
PricingRule (id, customer_id, product_id, price, min_qty, start_date, end_date, priority, created_at, updated_at)
Order (id, source, order_no, customer_id, order_date, issuer_company_id, currency, memo, created_at, updated_at)
OrderItem (id, order_id, product_id, qty, unit_price, tax_rate, discount, subtotal_ex_tax, tax_amount, total_in_tax, created_at, updated_at)
Invoice (id, invoice_no, issuer_company_id, customer_id, period_start, period_end, issue_date, due_date, subtotal_ex_tax, tax_amount, total_in_tax, status, notes, pdf_url, created_at, updated_at)
InvoiceItem (id, invoice_id, product_id, description, qty, unit_price, tax_rate, discount, subtotal_ex_tax, tax_amount, total_in_tax, created_at, updated_at)
User (id, email, name, role, is_active, last_login_at, created_at, updated_at)
AuditLog (id, actor_user_id, action, target_table, target_id, diff_json, created_at)
ImportJob (id, job_type, status, upload_id, filename, file_type, mapping_json, total_rows, processed_rows, error_count, warnings, errors, result_data, error_report_url, started_at, finished_at, completed_at, created_at, updated_at)
```

### 主要ポイント
- **CustomerCompany.is_individual**: AI判定による法人/個人フラグ（2025-10-24追加）
- **PricingRule**で会社別単価を柔軟に上書き（期間/数量/優先度）。
- **OrderItem.unit_price** は入力保存（CSV側に単価があれば採用、なければルール評価）。
- **税率**は品目/行単位で保持。請求書生成時に再計算し整合チェック。
- **ImportJob.result_data**: 解析結果をJSON形式で保存（列情報、サンプルデータ、メタデータ）

### インデックス例
- `CustomerCompany(is_individual)` - 法人/個人で絞り込み
- `Order(customer_id, order_date)`
- `OrderItem(order_id)`
- `PricingRule(customer_id, product_id, start_date, end_date, priority)`
- `Invoice(invoice_no UNIQUE)`
- `ImportJob(status, created_at)` - ジョブ一覧表示の高速化

### フィールド詳細補足

**CustomerCompany:**
- `is_individual`: Boolean, indexed - 法人（False）または個人（True）を識別
  - AI判定機能により自動設定（`app/ai/openai_provider.py`）
  - 手動での上書きも可能
  - 請求書フォーマットの切り替えに使用

**ImportJob:**
- `upload_id`: アップロードファイルの一意識別子
- `filename`: 元のファイル名
- `file_type`: csv, excel, pdf, txt, image
- `result_data`: JSON - `{"columns": [...], "data_sample": [...], "metadata": {...}}`
- `warnings`: JSON配列 - 警告メッセージ（AI判定結果など）
- `errors`: JSON配列 - エラーメッセージ
