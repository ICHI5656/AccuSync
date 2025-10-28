# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

**AccuSync（あきゅシンク）** は、多様なフォーマット（CSV/Excel/PDF/TXT/画像）から受注データを取り込み、AI判断機能で自動処理し、請求書・納品書PDFを生成するBtoB向け内製ツールです。

## 開発コマンド

### Docker環境（推奨）

```bash
# すべてのサービスを起動（初回はビルドも実行）
./RUN.sh

# または手動で
docker-compose up -d --build

# ログ確認
docker-compose logs -f [api|celery_worker|frontend|db|redis]

# サービス再起動
docker-compose restart [api|celery_worker|frontend]

# すべて停止
docker-compose down

# データも削除して完全クリーンアップ
docker-compose down -v
```

### バックエンド開発

```bash
cd backend

# データベースマイグレーション作成
docker-compose exec api alembic revision --autogenerate -m "description"

# マイグレーション適用
docker-compose exec api alembic upgrade head

# ロールバック
docker-compose exec api alembic downgrade -1

# データベース直接アクセス
docker-compose exec db psql -U accusync -d accusync

# Celeryワーカー再起動（ImportService変更時に必要）
docker-compose restart celery_worker

# APIコンテナ内でPythonスクリプト実行
docker-compose exec api python -c "import statement"

# 仮想環境での開発（ローカル）
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### フロントエンド開発

```bash
cd frontend

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# 本番モード起動
npm start

# Linting
npm run lint

# 型チェック
npm run typecheck
```

### テストデータ

```bash
# testdata/ ディレクトリにサンプルCSV/Excel/PDFあり
# ファイルアップロードAPIでテスト可能
curl -X POST "http://localhost:8100/api/v1/imports/upload" \
  -F "file=@testdata/sample.csv" \
  -F "file_type=csv"
```

## アーキテクチャの重要ポイント

### マイクロサービス構成

```
┌─────────────────┐
│   Frontend      │  Next.js 14 (App Router) - http://localhost:3100
│  (port 3100)    │
└────────┬────────┘
         │
         ↓ REST API
┌─────────────────┐
│   API Server    │  FastAPI + Uvicorn - http://localhost:8100
│  (port 8100)    │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ↓         ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  DB    │ │ Redis  │ │ Celery │ │ MinIO  │
│ :5433  │ │ :6380  │ │ Worker │ │ :9100  │
└────────┘ └────────┘ └────────┘ └────────┘
```

**注意:** すべてのポートは標準ポートと競合しないように調整済み

### データフロー（インポート処理）

1. **ファイルアップロード** (`/api/v1/imports/upload`)
   - APIが`/tmp/accusync_uploads/`にファイル保存
   - Docker volumeで`api`と`celery_worker`が共有

2. **ジョブ作成** (`/api/v1/imports/jobs`)
   - ImportJobレコード作成（status: pending）
   - Celeryタスク`process_file_import`をキューに追加

3. **ファイル解析** (Celeryバックグラウンド)
   - `app/parsers/factory.py`が適切なパーサーを選択
   - CSVParser/ExcelParser/PDFParser/TextParserが解析
   - AI自動マッピング（オプション）
   - 結果を`ImportJob.result_data`に保存（status: completed）

4. **データベースインポート** (`import_parsed_data` タスク)
   - `app/services/import_service.py`がデータをDB保存
   - 顧客・商品の自動作成
   - **AI顧客タイプ判定**（会社 vs 個人）
   - Order/OrderItem作成

### AI統合アーキテクチャ

**プロバイダー抽象化:**
```
AIProviderFactory
    ↓
AIProvider (base.py)
    ├─ OpenAIProvider (openai_provider.py)
    └─ ClaudeProvider (claude_provider.py)
```

**主要な機能:**
- `detect_file_format()`: ファイル形式自動判別
- `extract_data()`: 非構造化データ抽出
- `auto_map_columns()`: 列名自動マッピング
- `check_data_quality()`: データ品質チェック
- `classify_customer_type()`: 顧客タイプ判定（法人/個人）

**使用例:**
```python
from app.ai.factory import AIProviderFactory

ai_provider = AIProviderFactory.create()
result = await ai_provider.classify_customer_type(
    customer_name="株式会社テスト",
    additional_info={"phone": "03-1234-5678"}
)
# result.is_individual: False (法人)
# result.confidence: 0.95
# result.reason: "「株式会社」という法人格が含まれる"
```

### データモデル関係図

```
CustomerCompany (取引先会社・個人)
    ├─ is_individual: Boolean  # 法人/個人フラグ
    ├─ Orders (1:N)
    ├─ Invoices (1:N)
    └─ PricingRules (1:N)

IssuerCompany (請求者会社)
    ├─ Orders (1:N)
    └─ Invoices (1:N)

Product (商品マスタ)
    ├─ sku: String (商品コード)
    ├─ OrderItems (1:N)
    ├─ InvoiceItems (1:N)
    └─ PricingRules (1:N)

Order (受注)
    ├─ source: String (csv, manual, api)
    ├─ order_no: String (注文番号)
    └─ OrderItems (1:N)

Invoice (請求書)
    ├─ invoice_no: String (請求書番号)
    ├─ issue_date: Date
    ├─ payment_due_date: Date
    └─ InvoiceItems (1:N)

ImportJob (インポートジョブ)
    ├─ status: String (pending, processing, completed, failed)
    ├─ result_data: JSON (解析結果)
    └─ warnings/errors: JSON
```

### 重要な実装ノート

**1. ImportService での Decimal 使用**
```python
# 金額計算は必ずDecimalを使用
from decimal import Decimal
quantity = int(parse_number(row.get('数量')))
unit_price = Decimal(str(parse_number(row.get('単価'))))
subtotal = Decimal(quantity) * unit_price
```

**2. OrderItemはOrderモデルに含まれる**
```python
# 正しいインポート
from app.models.order import Order, OrderItem

# 誤り
from app.models.order_item import OrderItem  # このファイルは存在しない
```

**3. Product モデルは `sku` フィールドを使用**
```python
# 正しい
product = Product(sku="PROD001", name="商品A", default_price=Decimal("1000"))

# 誤り
product = Product(code="PROD001", ...)  # codeフィールドは存在しない
```

**4. Order モデルの必須フィールド**
```python
# source, order_no, order_date は必須
order = Order(
    customer_id=customer.id,
    source='csv',  # csv, manual, api
    order_no='ORD20251024001',
    order_date=datetime.now().date(),  # Date型（datetimeではない）
    memo='備考'
)
```

**5. Async/Sync ブリッジング**
```python
# ImportServiceなど同期コンテキストでAI機能を使う場合
import asyncio
result = asyncio.run(ai_provider.classify_customer_type(...))
```

**6. Celery ワーカーのコード更新**
```bash
# ImportServiceやタスク定義を変更した場合は必ず再起動
docker-compose restart celery_worker
```

**7. Docker ボリューム共有**
```yaml
# api と celery_worker は upload_temp ボリュームを共有
volumes:
  - upload_temp:/tmp/accusync_uploads
```

**8. WeasyPrint 依存関係問題**
```python
# PDFService は現在システムライブラリ依存で無効化
# app/services/__init__.py でコメントアウト済み
```

## 環境変数

重要な環境変数（`.env`ファイル）:

```env
# AI Provider
AI_PROVIDER=openai  # openai, claude
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
POSTGRES_USER=accusync
POSTGRES_PASSWORD=accusync_pass
POSTGRES_DB=accusync

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# MinIO (S3互換)
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=accusync
```

## テスト・デバッグ

### API テスト
```bash
# Swagger UI で対話的にテスト
http://localhost:8100/docs

# curlでテスト
curl http://localhost:8100/api/v1/health
```

### データベース確認
```bash
# PostgreSQL直接アクセス
docker-compose exec db psql -U accusync -d accusync

# テーブル一覧
\dt

# 顧客データ確認
SELECT id, name, is_individual FROM customer_companies;

# インポートジョブ確認
SELECT id, filename, status, total_rows FROM import_jobs;
```

### Celery タスク監視
```bash
# Celery ワーカーログ
docker-compose logs -f celery_worker

# タスクを手動トリガー
docker-compose exec celery_worker python -c "
from app.tasks.import_tasks import import_parsed_data
result = import_parsed_data.delay(job_id=1)
print(result.id)
"
```

### フロントエンド デバッグ
```bash
# Next.js ログ
docker-compose logs -f frontend

# ブラウザコンソールでAPIレスポンス確認
# Network タブで /api/v1/* リクエストを監視
```

## トラブルシューティング

**問題: "No such file or directory" エラー**
- 原因: api と celery_worker 間でファイルが共有されていない
- 解決: `docker-compose.yml` に `upload_temp` ボリュームが設定されているか確認
- 再起動: `docker-compose down && docker-compose up -d`

**問題: AI判定が動作しない（すべて法人になる）**
- 原因: OpenAI APIレート制限（429エラー）
- 確認: `docker-compose logs celery_worker | grep "429"`
- 対処: APIキーの確認、レート制限の解除待ち、別のプロバイダーに切り替え

**問題: マイグレーションエラー**
- 原因: モデル変更が反映されていない
- 解決:
  ```bash
  docker-compose exec api alembic revision --autogenerate -m "fix"
  docker-compose exec api alembic upgrade head
  ```

**問題: フロントエンドがAPIに接続できない**
- 確認: `http://localhost:8100/api/v1/health` にアクセス可能か
- 原因: APIコンテナが起動していない
- 解決: `docker-compose up -d api`

### 商品・価格管理機能

**商品マスタ管理** (`/api/v1/products`)
- 商品は事前登録が必須（インポート時の自動作成は無効化）
- SKUまたは商品名で検索・照合
- 標準単価、税率、税区分、単位を設定

**顧客別価格ルール** (`/api/v1/products/pricing`)
```python
# 価格ルールの作成例（product_id指定）
rule = PricingRule(
    customer_id=1,
    product_id=10,
    price=Decimal("800"),  # 顧客別特別価格
    min_qty=10,            # 最小注文数量
    start_date="2025-01-01",
    end_date="2025-12-31",
    priority=0
)

# 価格ルールの作成例（product_type_keyword指定）
rule = PricingRule(
    customer_id=1,
    product_type_keyword="ハードケース",  # 商品タイプキーワード
    price=Decimal("600"),  # 顧客別特別価格
    priority=0
)
```

**価格マトリクスページ** (`/pricing-matrix`)
- グリッド形式で会社別×商品タイプ別の卸単価を一括管理
- 商品タイプ（行）× 取引先（列）のマトリクス表示
- 各セルで直接価格入力・保存・削除が可能
- `product_type_keyword` を使用した価格ルール管理

**インポート時の価格適用優先順位:**
1. **価格マトリクスの設定値**（最優先）- `product_type_keyword` でマッチング
2. 商品マスタの標準単価（`default_price` > 0の場合）
3. CSVファイルの単価（フォールバック）

**インポート時の商品照合:**
1. SKUで検索（優先）
2. 商品名で検索（フォールバック）
3. 見つからない場合はスキップ（ワーニング表示）

**商品タイプキーワード抽出:**
- `_extract_product_keywords()` が商品名から商品タイプとバリエーションのみを抽出
- デザイン名は除外され、同じ商品タイプは同じ価格になる
- 例: "ハードケース(ボタニカル 青黄花柄)" → "ハードケース"
- 例: "手帳型カバーmirror(刺繍風プリント)" → "手帳型カバー / mirror"

### 列マッピング機能

**マッピングテンプレート** (`/api/v1/mapping`)
- 25フィールド対応（必須4、オプション21）
- テンプレート保存・再利用機能
- ファイル形式別のテンプレート管理

**フィールド一覧:**
- 必須: 顧客名、商品名、数量、単価
- オプション: 顧客コード、住所、郵便番号、電話、メール、商品SKU、注文番号、注文日、納品日、小計、税率、税額、合計、備考、割引、送料など

**マッピング表示の挙動:**
- マッピング前: CSV元の列名を全て表示
- マッピング後: マッピングされた列のみ表示（日本語ラベル + 元列名）

### AI設定画面

**設定確認** (`/api/v1/settings/ai`)
- 現在のAIプロバイダー（OpenAI / Claude）
- APIキー設定状況の確認
- 機能の有効/無効状態表示

**設定変更方法:**
1. `.env`ファイルを編集
2. `docker-compose restart api celery_worker`
3. 設定画面でリロードして確認

**注意:** AI設定は環境変数で管理（フロントエンドからの変更不可）

## 最近の主要な変更

**2025-10-28: 価格マトリクスページ実装**
- 会社別卸単価設定ページ作成（グリッド形式UI）
- `product_type_keyword` による価格ルール管理
- インポートエラー表示の改善（3段階表示：エラー/成功/警告）
- プレビュー表示の簡略化（必須フィールドのみ表示）
- 商品タイプキーワード抽出のリファイン（デザイン名除外）
- ホームページに価格マトリクスへのリンク追加

**2025-10-27: 商品・価格管理機能実装**
- 商品マスタ管理API・UI作成
- 顧客別価格ルール設定機能
- インポート時の商品参照機能（事前登録必須）
- 列マッピングテンプレート機能
- AI設定画面の改善（環境変数からの読み取り）
- 顧客管理ページ作成（締め日・支払い日設定）
- 顧客識別子システム追加（自動検出機能）

**2025-10-24: AI顧客タイプ判定機能追加**
- `CustomerCompany.is_individual` フィールド追加
- `AIProvider.classify_customer_type()` メソッド実装
- ImportService に AI判定統合

**主要な修正:**
- ImportJob モデルフィールド名統一（filename, total_rows, processed_rows）
- Decimal型による金額計算統一
- Docker ボリューム共有設定追加
- WeasyPrint 依存関係の一時無効化
- 商品自動登録機能の削除（事前登録必須化）
- order_date フィールドを標準フィールドに追加

## アクセスURL

| サービス | URL | 説明 |
|---------|-----|------|
| Frontend | http://localhost:3100 | メインUI |
| Backend API | http://localhost:8100 | REST API |
| API Docs | http://localhost:8100/docs | Swagger UI |
| MinIO Console | http://localhost:9101 | ストレージ管理（admin/minioadmin） |

## 主要な画面

| 画面 | URL | 機能 |
|-----|-----|------|
| ホーム | http://localhost:3100 | ダッシュボード |
| データ取り込み | http://localhost:3100/imports | CSV/Excel/PDFインポート |
| ジョブ一覧 | http://localhost:3100/jobs | インポートジョブ管理 |
| 商品管理 | http://localhost:3100/products | 商品マスタ・価格設定 |
| 価格マトリクス | http://localhost:3100/pricing-matrix | 会社別卸単価設定 |
| 顧客管理 | http://localhost:3100/customers | 取引先情報・締め日・支払い日設定 |
| 注文一覧 | http://localhost:3100/orders | 取り込んだ注文データ表示 |
| システム設定 | http://localhost:3100/settings | AI設定・請求者情報・DB統計 |

## 残りの開発タスク

1. **PDF生成機能修復** - WeasyPrint システム依存関係の解決
2. **AI判定の動作確認** - 実データでのテスト実施
