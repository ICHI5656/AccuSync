# 🚀 AccuSync クイックスタート

## 即座に起動する（3コマンド）

```bash
# 1. プロジェクトディレクトリに移動
cd /home/local-quest/claude-projects/AccuSync

# 2. 起動スクリプトを実行
./RUN.sh

# 3. ブラウザでアクセス
# Frontend: http://localhost:3100
# API Docs: http://localhost:8100/docs
```

## ✅ 設定済みの内容

### AI機能
- ✅ **OpenAI GPT-4o** が設定済み
- ✅ すべてのAI機能が有効化済み
  - ファイル形式自動判別
  - 非構造化データ抽出（PDF/TXT/画像対応）
  - 自動データマッピング
  - データ品質チェック

### システム構成
- ✅ **全サービス Docker対応**（ポート競合なし）
- ✅ **PostgreSQL** データベース（11テーブル）
- ✅ **Redis** キャッシュ＆ジョブキュー
- ✅ **MinIO** S3互換ストレージ
- ✅ **FastAPI** バックエンドAPI
- ✅ **Next.js** フロントエンド（ソフトグリーン基調）
- ✅ **Celery** 非同期タスク処理

### テンプレート
- ✅ **請求書** PDF生成（インボイス制度対応）
- ✅ **納品書** PDF生成
- ✅ 柔らかいデザイン（事務員向け）

## 📍 アクセスURL

| サービス | URL | 用途 |
|---------|-----|------|
| **Frontend** | http://localhost:3100 | メインUI（ファイルアップロード等） |
| **API Docs** | http://localhost:8100/docs | APIドキュメント（Swagger UI） |
| **Health Check** | http://localhost:8100/health | システム状態確認 |
| **MinIO Console** | http://localhost:9101 | ストレージ管理（minioadmin/minioadmin） |

## 🧪 動作テスト

### 1. システムヘルスチェック

```bash
curl http://localhost:8100/health
```

期待される結果：
```json
{
  "status": "healthy",
  "app": "AccuSync",
  "version": "0.1.0"
}
```

### 2. AI機能テスト（Python）

```bash
docker-compose exec api python << 'EOF'
from app.ai.factory import AIProviderFactory
import asyncio

async def test_ai():
    provider = AIProviderFactory.create("openai")

    # ファイル形式検出テスト
    result = await provider.detect_file_format(
        b"",
        "test.csv",
        ".csv"
    )
    print(f"ファイル形式検出: {result.file_type} (信頼度: {result.confidence})")

asyncio.run(test_ai())
EOF
```

### 3. PDF生成テスト

```bash
docker-compose exec api python << 'EOF'
from app.services.pdf_service import PDFService
from datetime import datetime

pdf_service = PDFService()

invoice_data = {
    "invoice_no": "INV-TEST-001",
    "issue_date": datetime(2025, 10, 24),
    "due_date": datetime(2025, 11, 24),
    "period_start": datetime(2025, 10, 1),
    "period_end": datetime(2025, 10, 31),
    "issuer": {
        "name": "AccuSync株式会社",
        "tax_id": "T1234567890123",
        "address": "東京都渋谷区渋谷1-1-1",
        "tel": "03-1234-5678",
        "email": "info@accusync.com",
        "bank_info": "みずほ銀行 渋谷支店 普通 1234567"
    },
    "customer": {
        "name": "株式会社テスト",
        "person": "山田太郎",
        "address": "東京都千代田区丸の内1-1-1",
        "email": "yamada@test.com"
    },
    "items": [
        {
            "description": "iPhone 15 カードタイプケース",
            "qty": 100,
            "unit": "個",
            "unit_price": 2480,
            "subtotal_ex_tax": 248000,
            "tax_rate": 0.1
        }
    ],
    "subtotal_ex_tax": 248000,
    "tax_amount": 24800,
    "total_in_tax": 272800,
    "payment_terms": "月末締め翌月末払い",
    "notes": "お振込手数料はご負担ください"
}

pdf_bytes = pdf_service.generate_invoice_pdf(invoice_data, "/tmp/test_invoice.pdf")
print(f"✅ PDF生成成功: {len(pdf_bytes)} bytes → /tmp/test_invoice.pdf")
EOF
```

生成されたPDFを確認：
```bash
docker cp accusync-api:/tmp/test_invoice.pdf ./test_invoice.pdf
```

### 4. データベース接続テスト

```bash
docker-compose exec db psql -U accusync -d accusync -c "SELECT version();"
```

## 📂 テストデータの使用

`testdata/` ディレクトリには実際のサンプルファイルがあります：

```bash
# テストデータ一覧
ls -lh testdata/

# 主なファイル:
# - CSV形式: 2025-10-17注文書.csv
# - Excel形式: 251010株式会社Quest様注文書.xlsx
# - PDF形式: クエスト発注書2024.2.29.pdf
# - TXT形式: 青江注文.txt
```

これらのファイルでAI機能をテストできます（フロントエンド実装後）。

## 🛠️ よく使うコマンド

### ログ確認
```bash
# 全サービスのログ
docker-compose logs -f

# API のログのみ
docker-compose logs -f api

# Frontend のログのみ
docker-compose logs -f frontend
```

### コンテナの状態確認
```bash
docker-compose ps
```

### データベース操作
```bash
# PostgreSQLに接続
docker-compose exec db psql -U accusync -d accusync

# テーブル一覧
docker-compose exec db psql -U accusync -d accusync -c "\dt"

# データ確認
docker-compose exec db psql -U accusync -d accusync -c "SELECT * FROM users LIMIT 5;"
```

### 再起動
```bash
# 全サービス
docker-compose restart

# 特定サービス
docker-compose restart api
docker-compose restart frontend
```

### 停止
```bash
# コンテナを停止
docker-compose down

# コンテナ＋ボリューム削除（完全リセット）
docker-compose down -v
```

## 🎨 UI カスタマイズ

フロントエンドのカラーは `frontend/tailwind.config.ts` で設定されています：

```typescript
colors: {
  accent: '#6bb89c',  // ソフトグリーン（メインカラー）
  ink: '#203036',     // ダークグレー（テキスト）
  muted: '#5b6b72',   // ミュートグレー（サブテキスト）
  line: '#e7efea',    // 淡いグリーン（罫線）
}
```

## 🔧 AI設定のカスタマイズ

AI機能は `config/ai_settings.yaml` で細かく調整できます：

```yaml
# AI Provider選択
default_provider: openai  # openai, claude, multi

# 機能の個別ON/OFF
features:
  file_format_detection:
    enabled: true
    confidence_threshold: 0.8

  data_extraction:
    enabled: true
    confidence_threshold: 0.85

  auto_mapping:
    enabled: true

  data_quality_check:
    enabled: true

# コスト制御
cost_control:
  monthly_budget: 100.0  # USD
```

## 📚 次のステップ

1. **フロントエンドでファイルアップロード機能を実装**
2. **testdata のファイルでAI機能をテスト**
3. **マスタデータ（発行会社、取引先、商品）を登録**
4. **請求書を生成して確認**

## 💡 Tips

- **開発時**: ファイルを編集すると自動的にリロードされます
- **DB変更時**: `alembic revision --autogenerate` でマイグレーション生成
- **AI機能OFF**: 環境変数 `AI_ENABLE_*=false` で個別に無効化可能
- **ポート変更**: `docker-compose.yml` の ports セクションで調整可能

---

**準備完了！すぐに開発を始められます** 🚀
