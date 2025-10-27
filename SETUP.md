# AccuSync セットアップガイド

## 🎯 現在の実装状況

### ✅ 完成している機能

#### Phase 1: 基盤構築
- [x] プロジェクト構造（backend/ frontend/ templates/ config/）
- [x] Docker環境（PostgreSQL、Redis、MinIO、API）
- [x] データベースモデル（全11テーブル）
  - IssuerCompany（発行会社）
  - CustomerCompany（取引先）
  - Product（商品）
  - PricingRule（単価ルール）
  - Order / OrderItem（受注）
  - Invoice / InvoiceItem（請求書）
  - User（ユーザー）
  - AuditLog（監査ログ）
  - ImportJob（インポートジョブ）
- [x] Alembicマイグレーション設定
- [x] FastAPI基本セットアップ
- [x] JWT認証システム

#### Phase 2: AI統合
- [x] AI統合層アーキテクチャ（アダプターパターン）
- [x] OpenAIプロバイダー実装
- [x] Claudeプロバイダー実装
- [x] AIプロバイダーファクトリー
- [x] AI設定ファイル（config/ai_settings.yaml）

#### Phase 3: ビジネスロジック
- [x] 単価決定サービス（PricingService）
- [x] PDF生成サービス（PDFService）
- [x] 請求書・納品書HTMLテンプレート統合

### 🚧 次に実装が必要な機能

#### Phase 2: データ取り込み（優先度: 高）
- [ ] ファイルパーサー
  - [ ] CSVパーサー
  - [ ] Excelパーサー（.xlsx, .xls）
  - [ ] PDFパーサー
  - [ ] TXTパーサー
  - [ ] 画像パーサー（OCR）
- [ ] データ取り込みサービス
- [ ] Celery設定とタスク定義
- [ ] インポートAPI実装

#### Phase 3: フロントエンド（優先度: 高）
- [ ] Next.js プロジェクト初期化
- [ ] 認証UI（ログイン・ログアウト）
- [ ] ダッシュボード
- [ ] ファイルアップロード画面
- [ ] マスタ管理画面（発行会社、取引先、商品、単価ルール）
- [ ] 受注データ一覧・編集
- [ ] 請求書生成・一覧
- [ ] AI設定画面

#### Phase 4: API実装（優先度: 高）
- [ ] 認証API（/auth/login, /auth/me）
- [ ] マスタAPI（発行会社、取引先、商品、単価ルール）
- [ ] 受注API（一覧、詳細、作成、更新、削除）
- [ ] インポートAPI（CSV/ファイルアップロード）
- [ ] 請求書API（プレビュー、生成、PDF取得）
- [ ] 監査ログAPI

#### Phase 5: テスト（優先度: 中）
- [ ] ユニットテスト（pytest）
- [ ] testdataを使った統合テスト
- [ ] E2Eテスト（Playwright）

## 📋 セットアップ手順

### 1. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集：

```env
# Database
DATABASE_URL=postgresql://accusync:accusync_pass@db:5432/accusync

# AI Provider
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# または Claude
# AI_PROVIDER=claude
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Dockerコンテナの起動

```bash
# コンテナをビルド＆起動
docker-compose up -d --build

# ログを確認
docker-compose logs -f api
```

### 3. データベースマイグレーション

```bash
# 初回のみ：マイグレーションファイルを生成
docker-compose exec api alembic revision --autogenerate -m "Initial migration"

# マイグレーションを適用
docker-compose exec api alembic upgrade head
```

### 4. 動作確認

```bash
# API ヘルスチェック
curl http://localhost:8000/health

# API ドキュメント
open http://localhost:8000/docs  # macOS
# または
xdg-open http://localhost:8000/docs  # Linux
```

## 🧪 テストデータの使用

`testdata/` ディレクトリには実際のサンプルファイルがあります：

- CSV形式: `2025-10-17注文書.csv`
- Excel形式: `251010株式会社Quest様注文書.xlsx`
- PDF形式: `クエスト発注書2024.2.29.pdf`
- TXT形式: `青江注文.txt`

これらのファイルでAI機能とパーサーをテストできます。

## 🔧 開発ワークフロー

### バックエンド開発

```bash
# ローカルで開発する場合
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### データベース操作

```bash
# PostgreSQLに接続
docker-compose exec db psql -U accusync -d accusync

# テーブル一覧
\dt

# データ確認
SELECT * FROM users LIMIT 5;
```

### AI機能のテスト

```python
# Python対話シェル
docker-compose exec api python

from app.ai.factory import AIProviderFactory

# OpenAIプロバイダーを取得
provider = AIProviderFactory.create("openai")

# ファイル形式検出テスト
import asyncio
result = asyncio.run(provider.detect_file_format(
    b"",
    "test.csv",
    ".csv"
))
print(result)
```

### PDF生成テスト

```python
from app.services.pdf_service import PDFService
from datetime import datetime

pdf_service = PDFService()

invoice_data = {
    "invoice_no": "INV-2025-001",
    "issue_date": datetime(2025, 10, 24),
    "due_date": datetime(2025, 11, 24),
    "period_start": datetime(2025, 10, 1),
    "period_end": datetime(2025, 10, 31),
    "issuer": {
        "name": "株式会社AccuSync",
        "tax_id": "T1234567890123",
        "address": "東京都渋谷区...",
        "tel": "03-1234-5678",
        "email": "info@accusync.com",
        "bank_info": "○○銀行 △△支店 普通 1234567"
    },
    "customer": {
        "name": "株式会社サンプル",
        "person": "山田太郎",
        "address": "東京都千代田区...",
        "email": "yamada@sample.com"
    },
    "items": [
        {
            "description": "iPhone 15 カードタイプ ミラー付き",
            "qty": 10,
            "unit": "個",
            "unit_price": 2480,
            "subtotal_ex_tax": 24800,
            "tax_rate": 0.1
        }
    ],
    "subtotal_ex_tax": 24800,
    "tax_amount": 2480,
    "total_in_tax": 27280,
    "payment_terms": "月末締め翌月末払い",
    "notes": "お振込手数料はご負担ください"
}

pdf_bytes = pdf_service.generate_invoice_pdf(
    invoice_data,
    output_path="test_invoice.pdf"
)

print(f"PDF生成完了: {len(pdf_bytes)} bytes")
```

## 🎨 UIデザイン仕様

### カラースキーム（テンプレート準拠）

```css
--accent: #6bb89c;   /* ソフトグリーン - メインカラー */
--ink: #203036;      /* ダークグレー - テキスト */
--muted: #5b6b72;    /* ミュートグレー - サブテキスト */
--bg: #ffffff;       /* 白 - 背景 */
--line: #e7efea;     /* 淡いグリーン - 罫線 */
```

### デザイン原則

1. **柔らかい印象**: 角丸（border-radius: 16px）と余白を重視
2. **視覚的階層**: カード型レイアウトで情報を整理
3. **信頼感**: 清潔感のある白ベース + ソフトグリーンアクセント
4. **読みやすさ**: 適切なフォントサイズと行間
5. **アクセシビリティ**: 十分なコントラスト比

### UI コンポーネント

- **ボタン**: 角丸、ホバー効果、明確なアクション表示
- **カード**: 影付き、角丸、グループ化された情報
- **テーブル**: シンプルな罫線、ヘッダー強調
- **フォーム**: 大きめの入力欄、明確なラベル
- **アラート**: 優しい色合いの通知（成功/警告/エラー）

## 📚 参考資料

- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [Next.js ドキュメント](https://nextjs.org/docs)
- [SQLAlchemy ドキュメント](https://docs.sqlalchemy.org/)
- [WeasyPrint ドキュメント](https://doc.courtbouillon.org/weasyprint/)
- [OpenAI API リファレンス](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)

## 🚀 次のステップ

1. **ファイルパーサーの実装**: testdataのファイルを解析できるようにする
2. **データ取り込みAPIの実装**: フロントエンドからファイルをアップロードできるようにする
3. **フロントエンドの構築**: モダンで使いやすいUIを実装
4. **テストの充実**: 実際のデータでE2Eテストを実施

---

**現在地点**: Phase 1〜2 完了（基盤構築 + AI統合）
**次の目標**: Phase 2〜3（データ取り込み + フロントエンド）
