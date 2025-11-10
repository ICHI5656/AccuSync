# PDF生成機能ガイド

## 概要

AccuSyncは**WeasyPrint**を使用して、請求書・納品書のPDFを生成します。

## 必要な環境

### Docker環境（推奨）
Dockerコンテナ内では、必要なシステムライブラリが自動的にインストールされます。

```bash
docker-compose up -d --build
```

### ローカル環境

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

pip install weasyprint==60.2
```

#### macOS
```bash
brew install cairo pango gdk-pixbuf libffi
pip install weasyprint==60.2
```

#### Windows
WeasyPrintはWindows上での動作が困難です。**Docker環境を使用してください**。

---

## API使用方法

### 請求書PDFを生成

```bash
# 請求書を作成
curl -X POST http://localhost:8100/api/v1/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "period_start": "2025-10-01",
    "period_end": "2025-10-31"
  }'

# レスポンス例
{
  "id": 1,
  "invoice_no": "INV-20251029-123456",
  ...
}

# PDFをダウンロード
curl -O http://localhost:8100/api/v1/invoices/1/pdf
```

### Pythonから直接使用

```python
from app.services.pdf_service import PDFService
from app.services.invoice_service import InvoiceService

# 請求書データを取得
invoice_data = InvoiceService.get_invoice_preview_data(db, invoice_id=1)

# PDFを生成
pdf_service = PDFService()
pdf_bytes = pdf_service.generate_invoice_pdf(invoice_data)

# ファイルに保存
with open("invoice.pdf", "wb") as f:
    f.write(pdf_bytes)
```

---

## テンプレート

### 請求書テンプレート
- **場所**: `templates/invoice.html`
- **デザイン**: ソフトグリーン基調、A4印刷最適化
- **機能**: インボイス制度対応、角丸カード型レイアウト

### 納品書テンプレート
- **場所**: `templates/delivery_note.html`
- **デザイン**: 請求書と統一されたデザイン
- **機能**: 配送先情報表示

### テンプレートのカスタマイズ

テンプレートはHandlebars風のプレースホルダーを使用しています：

```html
{invoice_no}               <!-- 請求書番号 -->
{issue_date}               <!-- 発行日 -->
{due_date}                 <!-- 支払期限 -->
{customer.name}            <!-- 顧客名 -->
{issuer.name}              <!-- 発行会社名 -->
{subtotal_ex_tax}          <!-- 税抜小計 -->
{tax_amount}               <!-- 消費税額 -->
{total_in_tax}             <!-- 税込合計 -->
```

テンプレートを編集する際は、`{変数名}` 形式を維持してください。
PDFServiceが自動的にJinja2形式に変換します。

---

## トラブルシューティング

### エラー: "PDF生成ライブラリが利用できません"

**原因**: WeasyPrintのシステムライブラリがインストールされていない

**解決策**:
1. Dockerコンテナを使用する（推奨）
2. ローカル環境の場合、必要なライブラリをインストール

```bash
# Dockerコンテナを再ビルド
docker-compose down
docker-compose up -d --build
```

### エラー: "ImportError: cannot import name 'HTML' from 'weasyprint'"

**原因**: WeasyPrintがインストールされていない

**解決策**:
```bash
pip install weasyprint==60.2
```

### PDFのフォントが正しく表示されない

**原因**: 日本語フォントが不足

**解決策**: Dockerfileにフォントを追加
```dockerfile
RUN apt-get install -y fonts-noto-cjk
```

### PDFのレイアウトが崩れる

**原因**: CSSがA4サイズに最適化されていない

**解決策**: `templates/invoice.html` の `@page` 設定を確認
```css
@page {
  size: A4;
  margin: 18mm;
}
```

---

## パフォーマンス

### 生成時間
- 平均: 500ms〜1秒
- 複雑な請求書（明細50件以上）: 1〜2秒

### メモリ使用量
- 1つのPDF生成: 約50MB
- 同時生成推奨数: 最大10件

### 最適化のヒント
```python
# 複数のPDFを生成する場合
pdf_service = PDFService()  # 1回だけインスタンス化

for invoice_id in invoice_ids:
    invoice_data = InvoiceService.get_invoice_preview_data(db, invoice_id)
    pdf_bytes = pdf_service.generate_invoice_pdf(invoice_data)
    # ... 保存処理
```

---

## よくある質問

**Q: PDFファイルのサイズはどのくらいですか？**
A: 通常、1枚あたり30〜100KB程度です。

**Q: カスタムフォントを使用できますか？**
A: はい、`templates/style.css` でWebフォントを指定できます。

**Q: 画像を挿入できますか？**
A: はい、テンプレートにHTMLの`<img>`タグを使用できます。

**Q: 複数ページの請求書を作成できますか？**
A: はい、WeasyPrintは自動的にページ分割します。

---

## 参考リンク

- [WeasyPrint公式ドキュメント](https://weasyprint.org/)
- [CSS Paged Media](https://www.w3.org/TR/css-page-3/)
- [テンプレートデザインガイド](./templates/README.md)
