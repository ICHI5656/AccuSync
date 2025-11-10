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

**9. デバイス検出サービス（DeviceDetectionService）**
```python
# backend/app/services/device_detection_service.py
# 商品名から機種情報、サイズ情報、商品タイプを自動抽出

from app.services.device_detection_service import DeviceDetectionService

service = DeviceDetectionService(db)

# 機種検出（iPhone, Galaxy, AQUOS, Xperia, Pixel など）
device, method, brand = service.detect_device_from_row(row)
# 例: ("AQUOS wish4", "product_name", "AQUOS")

# サイズ抽出（手帳型のみ）
size, method = service.extract_size_from_product_name(
    product_name="手帳型カバー/iPhone 8_i6",
    product_type="手帳型カバー",
    brand="iPhone",
    device="iPhone 8"
)
# 例: ("i6", "regex") または ("L", "device_master_db")

# 手帳構造タイプ抽出
structure = service.extract_notebook_structure("手帳型カバー/mirror")
# 例: "mirror", "ベルト無し", "両面印刷薄型"
```

**デバイス検出の優先順位:**
1. 機種専用列から検出（列名に「機種」「端末」などのキーワード）
2. 商品名列から検出
3. その他の列（備考、説明など）から検出

**サポートされる機種:**
- iPhone系（iPhone 15 Pro, iPhone 14 など）
- Galaxy系（Galaxy S23, A54 など）+ キャリアモデル番号（SC-, SCG-, SCV-）
- Xperia系 + キャリアモデル番号（SO-, SOG-, SOV-）
- AQUOS系（wish4, sense8, We2 など）+ キャリアモデル番号（SH-, SHG-, SHV-, A-SH）
- Pixel系（Pixel 8, Pixel 7a など）
- OPPO, Xiaomi, arrows など

**サイズ抽出の動作（ポータビリティ対応済み）:**
- **正規表現優先**: `_i6`, `_L`, `_M`, `_特大`, `_大` などのパターンを検出
- **ローカルDBフォールバック**: 正規表現で見つからない場合、`device_attributes`テーブルから取得
- **Supabase（オプション）**: ローカルDBにもない場合のみ外部DB検索（ネットワーク不要）
- **⚠️ 重要**: サイズ抽出は**手帳型カバーのみ**が対象（ハードケースは対象外）

**多店舗フォーマット対応（選択肢列からの機種抽出）:**
```python
# 選択肢列から機種とサイズを抽出
device, size, brand = service.extract_device_from_options(options_text)
```

**サポートされるフォーマット:**
1. **楽天形式（:セパレーター）**
   - `機種【iPhone】:iPhone 6[i6]`
   - `機種【AQUOS_2】:wish4(SH-52E)[3L]`

2. **楽天形式（=セパレーター）**
   - `機種【Google/OPPO/isai】=Pixel 8 a[L]`
   - ▼や-で始まる未選択項目は自動除外

3. **ワーマ形式**
   - `機種の選択(iPhone)=iPhone SE 第2世代 [i6]`

4. **Amazon形式（商品名から検出）**
   - `スマQ いphone14Pro 対応 ケース` → iPhone14Pro
   - `スマQ あくおす sense5G SH-53A` → AQUOS sense5
   - ひらがな表記（いふぉん、あくおす等）にも対応

**検出優先順位:**
1. 選択肢列のパターンマッチング（Pattern1/Pattern2）
2. 商品名列からの正規表現抽出
3. その他の列からの検出
4. サイズはローカルDB（device_attributes）から自動補完

**10. 機種マスターDB（DeviceMasterService）- ネットワーク非依存**
```python
# backend/app/services/device_master_service.py
# ローカルPostgreSQLを優先、Supabaseはオプション

from app.services.device_master_service import DeviceMasterService

service = DeviceMasterService(db)

# サイズ取得（ローカルDB優先）
size = service.get_device_size(brand="iPhone", device_name="iPhone 15 Pro")
# 返り値: "i6s" （ローカルDBから）

# 機種詳細情報取得
info = service.get_device_info(brand="AQUOS", device_name="AQUOS wish4")
# 返り値: {"brand": "AQUOS", "device_name": "AQUOS wish4",
#         "size_category": "M", "attribute_value": "Medium"}

# 接続テスト
results = service.test_connection()
# 返り値: {"local_db": True, "supabase": False}
```

**重要: 別のパソコンでの初期セットアップ**
```bash
# Docker起動後、必ず実行（機種マスターDBセットアップ）
./setup-device-master.sh  # Linux/Mac
setup-device-master.bat   # Windows

# これにより96機種のサイズ情報がローカルDBに登録され、
# ネットワーク環境に依存せず機種抽出・サイズ取得が動作します
```

**データベーステーブル構造:**
```sql
-- device_attributes: ローカル機種マスター（ネットワーク非依存）
CREATE TABLE device_attributes (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,        -- iPhone, Galaxy, AQUOS, etc.
    device_name VARCHAR(100) NOT NULL, -- iPhone 15 Pro, Galaxy A54, etc.
    size_category VARCHAR(20),         -- i6, L, M, 特大, etc.
    attribute_value VARCHAR(100),      -- Large, Medium, Small, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス（高速検索用）
CREATE INDEX idx_device_brand_name ON device_attributes (brand, device_name);

-- product_type_patterns: 商品タイプ学習テーブル（機械学習）
CREATE TABLE product_type_patterns (
    id SERIAL PRIMARY KEY,
    pattern VARCHAR(255) NOT NULL,         -- 商品名のパターン（部分一致）
    product_type VARCHAR(100) NOT NULL,    -- 商品タイプ（例: ハードケース）
    confidence FLOAT NOT NULL DEFAULT 1.0, -- 信頼度（0.0-1.0）
    source VARCHAR(50) NOT NULL DEFAULT 'manual', -- 'manual' or 'auto'
    usage_count INTEGER NOT NULL DEFAULT 0,       -- 使用回数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス（高速検索用）
CREATE INDEX idx_product_type_patterns_pattern ON product_type_patterns (pattern);
CREATE INDEX idx_product_type_patterns_product_type ON product_type_patterns (product_type);
CREATE INDEX idx_product_type_patterns_confidence ON product_type_patterns (confidence);
```

**優先順位（サイズ取得）:**
1. 正規表現パターン（商品名内の `_i6`, `_L` 等）
2. ローカルPostgreSQL `device_attributes` テーブル
3. Supabase（接続可能な場合のみ、オプション）

**11. 楽天SKU管理システムDB連携（RakutenSKUService）**
```python
# backend/app/services/rakuten_sku_service.py
# 外部プロジェクト csv_sku.k のDBから商品情報を取得

from app.services.rakuten_sku_service import RakutenSKUService

service = RakutenSKUService()  # デフォルト: /external_data/csv_sku.k/inventory.db

# SKU番号からサイズ取得（手帳型商品）
size = service.get_size_by_sku("sku_r00001")
# 返り値: "i6", "L", "M" など

# 機種名からサイズ取得（devices JOIN techo_sizes）
size = service.get_size_by_device(brand="iPhone", device_name="iPhone 15 Pro")
# 返り値: "i6s" （techo_sizesマスターから）

# デザイン番号から商品タイプ取得
product_type = service.get_product_type_by_design_number("ami_kaiser-A_1r-A")
# 返り値: "手帳型カバー", "ハードケース" など

# 接続テスト
is_available = service.test_connection()
# 返り値: True/False
```

**Docker環境でのボリュームマウント:**
```yaml
# docker-compose.yml で外部DBをマウント
volumes:
  - /mnt/c/Users/info/Desktop/sin/csv_sku.k/data:/external_data/csv_sku.k:ro
```

**外部DB構造（csv_sku.k）:**
- `techo_products`: SKU別の手帳型商品マスター（size_classification, compatible_device）
- `product_masters`: 商品番号別のマスター（product_type, available_sizes）
- `devices`: 機種マスター（device_name, brand_id, techo_size_id）
- `techo_sizes`: サイズマスター（SS, S, M, L, LL, 2L, 3L, i6）
- `brands`: ブランドマスター（name, display_name）

**12. 機種・サイズの機械学習機能**
```python
# backend/app/services/device_learning_service.py
# backend/app/services/size_learning_service.py
# ユーザーの手動変更を学習し、次回から自動適用

from app.services.device_learning_service import DeviceLearningService
from app.services.size_learning_service import SizeLearningService

# 機種の学習
device_learning = DeviceLearningService(db)
pattern = device_learning.learn_from_product_name(
    product_name="いphone14Pro ケース",
    device_name="iPhone 14 Pro",
    brand="iPhone",
    source="manual"  # 'manual' または 'auto'
)
# 信頼度: 手動=0.9, 自動=0.7

# 機種の予測
device, brand, confidence, method = device_learning.predict_device(
    product_name="いphone14Pro 対応"
)
# 返り値: ("iPhone 14 Pro", "iPhone", 0.9, "ml_manual")

# サイズの学習（手帳型のみ）
size_learning = SizeLearningService(db)
pattern = size_learning.learn_from_product_name(
    product_name="手帳型カバー/iPhone 8_i6",
    size="i6",
    device_name="iPhone 8",
    brand="iPhone",
    source="manual"
)

# サイズの予測
size, confidence, method = size_learning.predict_size(
    product_name="手帳型カバー/iPhone 8",
    device_name="iPhone 8"  # オプション: 機種指定でより高精度
)
# 返り値: ("i6", 0.95, "ml_manual")
```

**学習パターンDB:**
```sql
-- device_patterns: 機種学習テーブル
CREATE TABLE device_patterns (
    id SERIAL PRIMARY KEY,
    pattern VARCHAR(255) NOT NULL,         -- 商品名パターン
    device_name VARCHAR(100) NOT NULL,     -- 正しい機種名
    brand VARCHAR(50),                     -- ブランド
    confidence FLOAT NOT NULL DEFAULT 1.0, -- 信頼度（0.0-1.0）
    source VARCHAR(50) NOT NULL,           -- 'manual' or 'auto'
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- size_patterns: サイズ学習テーブル
CREATE TABLE size_patterns (
    id SERIAL PRIMARY KEY,
    pattern VARCHAR(255) NOT NULL,         -- 商品名パターン
    size VARCHAR(20) NOT NULL,             -- 正しいサイズ
    device_name VARCHAR(100),              -- オプション: 機種名
    brand VARCHAR(50),                     -- オプション: ブランド
    confidence FLOAT NOT NULL DEFAULT 1.0,
    source VARCHAR(50) NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**インポート時の統合優先順位:**

**機種検出:**
1. デザインマスター（商品番号から）
2. **機種学習パターン**（商品名から）← NEW
3. 通常の機種検出（選択肢列、機種列、商品名、その他）

**サイズ抽出（手帳型のみ）:**
1. **サイズ学習パターン**（商品名+機種から）← NEW
2. 商品属性正規表現（`_i6`, `_L` など）
3. **楽天SKU管理システムDB**（SKU番号から）← NEW
4. **楽天SKU管理システムDB**（機種名から）← NEW
5. ローカルDB（device_attributes）
6. Supabase（オプション）

**商品タイプ検出:**
1. ローカルDB（SKU）
2. Supabase曖昧検索
3. **楽天SKU管理システムDB**（デザイン番号から）← NEW
4. 商品タイプ学習パターン（SKU）
5. デザインマスター（商品名）
6. 商品タイプ学習パターン（商品名）
7. 正規表現フォールバック

**13. 機種マスターDB同期機能（Supabase→ローカルDB）**
```bash
# 1. 同期状態を確認
curl http://localhost:8100/api/v1/settings/device-master/status

# レスポンス例:
# {
#   "success": true,
#   "local_db": {
#     "count": 100,
#     "last_updated": "2025-11-07T06:49:36.482804"
#   },
#   "supabase": {
#     "available": false,  # Supabase接続可否
#     "count": 0
#   },
#   "sync_needed": false,  # 同期が必要かどうか
#   "timestamp": "2025-11-07T07:25:57.025472"
# }

# 2. 手動で同期を実行（SupabaseからローカルDBへ）
curl -X POST http://localhost:8100/api/v1/settings/device-master/sync

# レスポンス例:
# {
#   "success": true,
#   "synced_count": 150,      # 同期された機種数
#   "total_fetched": 150,     # Supabaseから取得した総数
#   "errors": [],
#   "error": null,
#   "timestamp": "2025-11-07T07:30:00.123456"
# }
```

**自動同期設定:**
- Celery Beatで**毎日1回**自動的にSupabaseと同期
- 新しい機種が追加された場合、自動的にローカルDBに反映
- 手動同期も可能（APIエンドポイント経由）

**UPSERT動作:**
- 既存の機種（brand + device_name）は更新
- 新しい機種は追加
- 削除された機種はそのまま残る（上書きのみ）

**Supabaseが利用不可の場合:**
- ローカルDBのデータをそのまま使用
- エラーは発生せず、警告のみログに出力
- 手動で`setup-device-master.sh`を実行すれば初期データを再登録可能

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

**問題: Dockerビルド時のパッケージエラー**
- エラー: `Package 'libgdk-pixbuf2.0-0' has no installation candidate`
- 原因: Debian trixieでパッケージ名が変更された
- 解決済み: `backend/Dockerfile`で`libgdk-pixbuf-2.0-0`を使用

**問題: Supabase依存関係の競合**
- エラー: `supabase 2.3.4 depends on httpx<0.26`
- 原因: httpxバージョンの不一致
- 解決済み: `requirements.txt`で`httpx>=0.24.0`, `supabase==2.16.0`を使用

**問題: Supabaseに接続できない（DNS解決エラー）**
- エラー: `[Errno -2] Name or service not known`
- 原因: WSL2のDNS設定または社内ネットワーク制限
- 影響: **なし** - ローカルDBと正規表現でサイズ抽出が正常に機能
- 対処: そのまま使用可能（Supabaseはオプション機能）
- 参考: `setup-device-master.sh/.bat` でローカルDBセットアップ済み

**問題: 別のパソコンで機種抽出が動作しない**
- 原因: `device_attributes` テーブルが未作成またはデータ未登録
- 確認: `docker-compose exec db psql -U accusync -d accusync -c "SELECT COUNT(*) FROM device_attributes;"`
- 解決: セットアップスクリプト実行
  ```bash
  # Linux/Mac
  ./setup-device-master.sh

  # Windows
  setup-device-master.bat
  ```
- 期待結果: 96件のデバイスデータが登録される

**問題: インポートプレビューで「サイズ情報が検出できませんでした」と表示される**
- 原因: ハードケース商品でもエラーメッセージが表示されていた（仕様として正しいが誤解を招く）
- 解決済み: フロントエンドで商品タイプに応じたメッセージに変更
  - ハードケース：「サイズ対象外（ハードケース等）」
  - 手帳型カバー未検出：「サイズ情報が検出できませんでした（手帳型のみサイズ対象）」
- **重要**: サイズ抽出は手帳型カバーのみが対象（ハードケースは対象外）

**問題: 楽天SKU管理システムDBに接続できない**
- 原因: Docker環境でボリュームマウントが正しく設定されていない
- 確認: `docker-compose exec api python -c "from pathlib import Path; print(Path('/external_data/csv_sku.k/inventory.db').exists())"`
- 解決: `docker-compose.yml` にボリュームマウントが追加されているか確認
  ```yaml
  volumes:
    - /mnt/c/Users/info/Desktop/sin/csv_sku.k/data:/external_data/csv_sku.k:ro
  ```
- 再起動: `docker-compose down && docker-compose up -d`

**問題: 機械学習機能が動作しない（学習パターンが保存されない）**
- 原因: `device_patterns` または `size_patterns` テーブルが未作成
- 確認: `docker-compose exec db psql -U accusync -d accusync -c "\dt"`
- 解決: マイグレーション実行
  ```bash
  docker-compose exec api alembic upgrade head
  ```
- 期待結果: `device_patterns` と `size_patterns` テーブルが存在する

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

### 商品タイプ機械学習機能

**概要:**
ユーザーが手動で変更した商品タイプのパターンを学習し、次回のインポート時に自動的に適用します。

**学習API** (`POST /api/v1/product-types/learn`)
```bash
# 商品タイプの学習
curl -X POST http://localhost:8100/api/v1/product-types/learn \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "手帳型カバー/mirror(刺繍風プリント)",
    "product_type": "手帳型カバー",
    "source": "manual"
  }'

# レスポンス:
# {
#   "success": true,
#   "message": "Pattern learned: 手帳型カバー → 手帳型カバー",
#   "pattern": {
#     "id": 1,
#     "pattern": "手帳型カバー",
#     "product_type": "手帳型カバー",
#     "confidence": 0.9,
#     "source": "manual",
#     "usage_count": 1
#   }
# }
```

**予測API** (`POST /api/v1/product-types/predict`)
```bash
# 商品タイプの予測
curl -X POST http://localhost:8100/api/v1/product-types/predict \
  -H "Content-Type: application/json" \
  -d '{"product_name": "手帳型カバー/rose(ローズ柄)"}'

# レスポンス:
# {
#   "product_type": "手帳型カバー",
#   "confidence": 0.9,
#   "detection_method": "ml_manual"
# }
```

**統計情報API** (`GET /api/v1/product-types/statistics`)
```bash
curl http://localhost:8100/api/v1/product-types/statistics

# レスポンス:
# {
#   "total_patterns": 3,
#   "manual_patterns": 3,
#   "auto_patterns": 0,
#   "total_usage": 7
# }
```

**パターン管理:**
- `GET /api/v1/product-types/patterns` - すべてのパターンを取得
- `GET /api/v1/product-types/patterns/{product_type}` - 特定の商品タイプのパターンを取得
- `DELETE /api/v1/product-types/patterns/{pattern_id}` - パターンを削除

**動作の仕組み:**
1. ユーザーが商品タイプを手動で変更
2. システムが商品名からパターンを抽出（例: "手帳型カバー"）
3. パターンと商品タイプの対応をDBに保存（confidence: 0.9）
4. 次回インポート時、同じパターンが含まれる商品名があれば自動的に商品タイプを適用
5. 使用回数がインクリメントされ、信頼度が徐々に上昇（最大1.0）

**信頼度スコア:**
- 手動学習: 0.9（ユーザーが明示的に設定）
- 自動学習: 0.7（システムが自動判定）
- 使用回数に応じて信頼度が上昇（+0.05/回）

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

**プレビュー表示の機種・サイズ情報:**
- 📱 機種列: `detected_device` + `detected_brand` を表示
  - 検出済み: 緑色背景、検出方法をツールチップに表示
  - 未検出: 赤色背景、「機種情報が検出できませんでした」
- 📏 サイズ列: `detected_size` を表示（**手帳型カバーのみ**）
  - 検出済み: 青色背景、検出方法（正規表現/Supabase DB）をツールチップに表示
  - 手帳型カバー未検出: グレー背景、「サイズ情報が検出できませんでした（手帳型のみサイズ対象）」
  - ハードケース: グレー背景、「サイズ対象外（ハードケース等）」

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

**2025-11-10: 楽天SKU管理システムDB統合と機械学習機能**
- `RakutenSKUService` 実装（外部プロジェクト csv_sku.k のDB連携）
- SKU番号・機種名からのサイズ抽出機能
- デザイン番号からの商品タイプ抽出機能
- `DeviceLearningService` 実装（機種の手動変更を学習）
- `SizeLearningService` 実装（サイズの手動変更を学習）
- `device_patterns` テーブル追加（機種学習パターン保存）
- `size_patterns` テーブル追加（サイズ学習パターン保存）
- Docker環境に外部DBボリュームマウント追加
- Amazonひらがな表記対応強化（`_pre_normalize_text()`）
- インポートプレビューに学習パターン予測機能統合
- 信頼度スコアリングシステム（手動: 0.9、自動: 0.7）

**2025-11-07: UI改善（サイズ列ツールチップ修正）**
- インポートプレビュー画面のサイズ列ツールチップを商品タイプに応じて改善
- ハードケース商品：「サイズ対象外（ハードケース等）」と表示
- 手帳型カバー（未検出）：「サイズ情報が検出できませんでした（手帳型のみサイズ対象）」と表示
- サイズ抽出が手帳型カバー専用であることを明確化し、誤解を防止

**2025-11-07: 商品タイプ機械学習機能実装**
- `product_type_patterns` テーブル追加（学習データ保存用）
- ProductTypeLearningService実装（パターン学習・予測エンジン）
- 商品タイプ学習API追加（`POST /api/v1/product-types/learn`）
- 商品タイプ予測API追加（`POST /api/v1/product-types/predict`）
- 統計情報API追加（`GET /api/v1/product-types/statistics`）
- パターン管理API追加（GET/DELETE /api/v1/product-types/patterns）
- ユーザーが手動変更した商品タイプを自動学習し、次回から適用
- 信頼度スコアリング機能（手動: 0.9、自動: 0.7）
- 使用回数によるパターン品質評価

**2025-11-07: 多店舗フォーマット対応（機種抽出の強化）**
- 選択肢列からの機種・サイズ抽出機能を追加（`extract_device_from_options()`）
- 楽天形式のセパレーター対応拡張（`:` および `=` の両方をサポート）
- ワーマ形式の選択肢パターンに対応（`機種の選択(ブランド)=機種名[サイズ]`）
- 未選択項目（▼や-で始まる）の自動除外機能
- ひらがな表記の機種名に対応（いふぉん、あくおす等）
- 商品名からの正規化検出を強化（スペースなし、ひらがな、カタカナ）
- スペース非依存のデバイス名正規化（`iPhone14Pro` ↔ `iPhone 14 Pro`）
- 統合テスト実装（楽天/ワーマ/Amazon全フォーマット: 8/8成功）

**2025-10-31: ポータビリティ対応（ネットワーク非依存化）**
- ローカルPostgreSQLに`device_attributes`テーブルを追加
- DeviceMasterService実装（ローカルDB優先、Supabaseはオプション）
- 96機種のサイズ情報をローカルDBに格納
- セットアップスクリプト作成（`setup-device-master.sh/.bat`）
- SETUP_GUIDE.md作成（別パソコンでの起動手順）
- 機種抽出・サイズ取得がネットワーク環境に依存しない構成に変更

**2025-10-30: インフラ修正とSupabase統合**
- Dockerfileのパッケージ名修正（`libgdk-pixbuf-2.0-0`）
- Supabaseパッケージを2.16.0にアップグレード
- httpx依存関係の競合を解決（`httpx>=0.24.0`）
- Supabaseサービスの初期化を改善（接続失敗時の自動フォールバック）
- サイズ抽出機能の動作確認完了（正規表現ベースで動作）

**2025-10-30: 注文統計ページ実装**
- 在庫管理用の5つの独立した統計ページを作成
- 件数統計と個数統計を明確に分離
- 共通レイアウトとReact Contextによるデータ共有
- サイドバーのクリック展開機能（ハードケース機種別・手帳ケースサイズ別）
- ハードケース（機種別）と手帳ケース（種類別にサイズ・機種で集計）の分類
- Next.js App Router のネストされたルート構造を活用

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
| **注文統計** | http://localhost:3100/stats | **在庫管理用の詳細統計情報** |
| システム設定 | http://localhost:3100/settings | AI設定・請求者情報・DB統計 |

### 注文統計ページ（/stats）

注文統計は在庫管理のために設計された5つの独立したページから構成されています：

| サブページ | URL | 説明 |
|-----------|-----|------|
| 📈 総計 | http://localhost:3100/stats | ハードケース/手帳ケース/全体の3カード表示 |
| 📋 件数統計 | http://localhost:3100/stats/count | 機種別・サイズ別の件数詳細リスト |
| 📦 個数統計 | http://localhost:3100/stats/quantity | 機種別・サイズ別の個数詳細リスト |
| 📊 件数サマリー | http://localhost:3100/stats/count-summary | 件数の概要とトップ5 |
| 🎯 個数サマリー | http://localhost:3100/stats/quantity-summary | 個数の概要とサイズ別トップ5 |

**🏢 取引先会社フィルタ機能**

サイドバーの「取引先会社」ドロップダウンで会社を選択すると、その会社の注文のみに絞り込めます：

- ✅ **すべて**: 全会社の注文統計を表示
- ✅ **Quest**: Questの注文のみを表示
- ✅ **その他の会社**: 選択した会社の注文のみを表示

**CSV取り込み時の取引先選択方法:**

1. **データ取り込み画面**（http://localhost:3100/imports）でCSVファイルをアップロード
2. **取引先会社を選択（オプション）**ドロップダウンを使用
   - 「（CSVのデータから自動作成）」：CSV内の顧客情報から新規作成
   - 既存の会社を選択（Quest等）：選択した会社で注文を登録
3. インポート実行

**使用例:**
```
Questの注文データをインポートする場合：
1. CSVアップロード
2. 「Quest（法人）」を選択
3. マッピング設定してインポート実行
→ 注文統計で「Quest」を選択すると、Questの注文のみ集計される
```

**統計ページの特徴:**
- **共通サイドバー**: 全ページで統計データを共有し、ページ間の移動が容易
- **件数 vs 個数の分離**: 注文件数（count）と商品個数（quantity）を明確に区別
- **展開可能なサマリー**: サイドバーの個数サマリーでハードケース（機種別）・手帳ケース（サイズ別）をクリック展開
- **リアルタイム更新**: データは一度だけフェッチされ、全ページで共有
- **商品タイプ別**: ハードケース（機種ごと）、手帳ケース（種類別にサイズと機種で集計）

**⚠️ 重要：在庫管理ロジック（手帳型カバーの構成）**

手帳型カバーは**2つの部品**で構成されます：
1. **手帳部分**（サイズ別）→ L, M, i6, 特大など
2. **ハードケース部分**（機種別）→ iPhone 15 Pro, AQUOS wish4など

**在庫計算式:**
```
手帳型カバー 1個 = 手帳サイズ部品 1個 + ハードケース部品 1個
```

**統計への反映:**
- ✅ **純粋なハードケース商品** → ハードケース統計のみに加算
- ✅ **手帳型カバー商品** → **手帳統計 + ハードケース統計の両方に加算**

**具体例:**
```
注文: 手帳型カバー/キャメル iPhone 15 Pro サイズL × 5個

必要な在庫:
- サイズLの手帳部分: 5個
- iPhone 15 Pro用ハードケース: 5個

統計への反映:
✅ 手帳サイズ「L」: +5個
✅ ハードケース「iPhone 15 Pro」: +5個（手帳用部品として）
```

**ハードケース統計の内訳:**
```
ハードケース統計 = 純粋なハードケース注文 + 手帳型カバー用ハードケース部品
```

これにより、在庫管理で**実際に必要なハードケース部品の総数**が正確に把握できます。

**データ構造:**
```typescript
// 統計API: GET /api/v1/stats/orders/detailed
{
  total_orders: number,
  hardcase_stats: [
    {
      device: string,      // 機種名
      count: number,       // 件数
      quantity: number,    // 個数
      by_date: [...]       // 日付別データ
    }
  ],
  notebook_stats_by_type: {
    "キャメル": {
      size_stats: [{ size: "L", count: 5, quantity: 15 }],
      device_stats: [{ device: "iPhone 8", count: 3, quantity: 10 }]
    }
  }
}
```

**実装パターン:**
- Next.js 14 App Router with nested routes
- Shared layout with React Context for data sharing
- TypeScript interfaces for type safety
- Conditional null checks with early return pattern

## ポータビリティのポイント

### ✅ ネットワーク非依存の機能（別のパソコンでも動作）

1. **機種抽出** - 正規表現パターンベース
2. **サイズ取得** - ローカルDB（device_attributes）から取得
3. **商品管理** - 全てローカルPostgreSQLで完結
4. **注文処理** - 外部APIに依存しない

### ⚠️ ネットワーク依存の機能（オプション）

1. **AI機能** - OpenAI/Claude APIキーが必要
   - 顧客タイプ判定
   - データ品質チェック
   - 自動マッピング
   → `.env`でAPIキーを設定すれば利用可能

2. **Supabaseクラウド** - 外部機種マスターDB
   - ローカルDBで代替可能
   - 影響なし

### 📋 別パソコンでのセットアップチェックリスト

- [ ] Docker Desktopがインストールされている
- [ ] `.env`ファイルが作成されている
- [ ] `docker-compose up -d`でサービスが起動
- [ ] `setup-device-master.sh(.bat)`を実行済み
- [ ] `http://localhost:3100`にアクセスできる
- [ ] データベースに機種マスターデータが登録されている（96件）
- [ ] テストCSVのインポートが成功する

詳細は `SETUP_GUIDE.md` を参照してください。

## 商品タイプ機械学習機能

### 概要
注文一覧画面で商品タイプを手動で変更すると、その変更内容を機械学習で自動的に学習します。
次回の同じ商品パターンのインポート時に、学習した商品タイプを自動的に適用します。

### データベース構造
```sql
CREATE TABLE product_type_patterns (
    id SERIAL PRIMARY KEY,
    pattern VARCHAR(255) NOT NULL,           -- 商品名から抽出したパターン
    product_type VARCHAR(100) NOT NULL,      -- 商品タイプ
    confidence FLOAT NOT NULL DEFAULT 1.0,   -- 信頼度（0.0-1.0）
    source VARCHAR(50) NOT NULL,             -- 'manual' または 'auto'
    usage_count INTEGER NOT NULL DEFAULT 0,  -- 使用回数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API エンドポイント

**商品タイプ更新（学習付き）:**
```bash
# 注文明細の商品タイプを更新し、自動的に学習
PUT /api/v1/orders/items/{order_item_id}/product-type
{
  "product_type": "手帳型カバー"
}

# レスポンス
{
  "success": true,
  "message": "Product type updated and learned: 手帳型カバー/mirror → 手帳型カバー",
  "order_item_id": 123,
  "old_product_type": null,
  "new_product_type": "手帳型カバー",
  "learned_pattern": {
    "pattern": "手帳型カバー",
    "confidence": 0.9,
    "usage_count": 1
  }
}
```

**パターン学習:**
```bash
POST /api/v1/product-types/learn
{
  "product_name": "手帳型カバー/mirror(刺繍風プリント)",
  "product_type": "手帳型カバー",
  "source": "manual"
}
```

**商品タイプ予測:**
```bash
POST /api/v1/product-types/predict
{
  "product_name": "手帳型カバー/rose(ローズ柄)"
}

# レスポンス
{
  "product_type": "手帳型カバー",
  "confidence": 0.95,
  "detection_method": "ml_manual"
}
```

**学習パターン一覧:**
```bash
GET /api/v1/product-types/patterns
GET /api/v1/product-types/patterns/{product_type}
DELETE /api/v1/product-types/patterns/{pattern_id}
GET /api/v1/product-types/statistics
```

### 学習メカニズム

1. **パターン抽出:**
   - 商品名から特徴的なキーワードを抽出
   - 商品タイプそのものをメインパターンとして保存

2. **信頼度スコアリング:**
   - 手動学習（manual）: 初期信頼度 0.9
   - 自動学習（auto）: 初期信頼度 0.7
   - 使用されるたびに信頼度が +0.05 増加（最大 1.0）

3. **予測ロジック:**
   - 商品名に含まれるパターンを部分一致で検索
   - 最も信頼度が高いパターンを選択
   - 使用回数をインクリメント

4. **統計情報:**
   - 総パターン数
   - 手動学習 vs 自動学習パターン数
   - 総使用回数

### UI 使用方法

1. 注文一覧ページ（`http://localhost:3100/orders`）を開く
2. 商品タイプ列の「編集」ボタンをクリック
3. 新しい商品タイプを入力
4. 「保存」ボタンをクリック
5. システムが自動的に学習し、成功メッセージを表示
6. 学習結果（パターン、信頼度、使用回数）が表示される

### 実装ファイル

**バックエンド:**
- `backend/app/models/product_type_pattern.py` - SQLAlchemyモデル
- `backend/app/services/product_type_learning_service.py` - 学習サービス
- `backend/app/api/v1/endpoints/product_types.py` - APIエンドポイント
- `backend/app/api/v1/endpoints/orders.py` - 商品タイプ更新エンドポイント
- `backend/alembic/versions/514c297c5ee1_add_product_type_patterns_table.py` - マイグレーション

**フロントエンド:**
- `frontend/app/orders/page.tsx` - 注文一覧ページ（編集UI）

### テスト方法

```bash
# 学習テスト
curl -X POST "http://localhost:8100/api/v1/product-types/learn" \
  -H "Content-Type: application/json" \
  -d '{"product_name":"手帳型カバー/mirror","product_type":"手帳型カバー","source":"manual"}'

# 予測テスト
curl -X POST "http://localhost:8100/api/v1/product-types/predict" \
  -H "Content-Type: application/json" \
  -d '{"product_name":"手帳型カバー/rose"}'

# パターン一覧
curl -X GET "http://localhost:8100/api/v1/product-types/patterns"

# 統計情報
curl -X GET "http://localhost:8100/api/v1/product-types/statistics"
```

**価格マトリクス連携機能（CSVプレビュー）**

CSVインポートのプレビュー時に、価格マトリクスに登録されている卸単価を自動的に表示します。

**APIレベルの実装:**
```python
# backend/app/api/v1/endpoints/imports.py
# プレビューリクエストにcustomer_idを追加
@router.post("/preview", response_model=ParsePreviewResponse)
async def preview_parse(request: ParsePreviewRequest, db: Session = Depends(get_db)):
    # customer_idが指定されている場合、価格マトリクスから価格を取得
    if request.customer_id and row.get('extracted_memo'):
        product_type_keyword = row['extracted_memo']
        pricing_rule = db.query(PricingRule).filter(
            PricingRule.customer_id == request.customer_id,
            PricingRule.product_type_keyword == product_type_keyword
        ).first()

        if pricing_rule:
            row['matrix_price'] = float(pricing_rule.price)
            row['price_source'] = 'matrix'
```

**プレビュー画面の列順（Amazon対応）:**
1. 📝 商品タイプ（extracted_memo）
2. 🏷️ ブランド（detected_brand）
3. 📱 機種（detected_device）
4. 📏 サイズ（detected_size）
5. 💰 **価格マトリクス（matrix_price）**← NEW
6. 🔢 **商品番号**（優先表示）← NEW
7. 📦 **商品タイトル**（優先表示）← NEW
8. その他のCSV列

**使い方:**
1. データ取り込み画面で取引先を選択してCSVアップロード
2. プレビューボタンをクリック
3. 価格マトリクスに設定がある商品タイプは緑色背景で卸単価が表示される
4. 設定がない場合は「-」（グレー背景）

**重要な商品タイプ検出ルール（Amazon）:**
```python
# backend/app/services/import_service.py の _extract_product_keywords()

# 優先順位1: SKUに「kaiser」が含まれる場合
if 'kaiser' in product_sku_lower:
    return '手帳型kaiser'

# 優先順位2: card/mirrorで手帳型ケース判定（Amazonルール）
is_amazon_notebook = (
    'カード' in product_name or 'card' in product_name_lower or
    'ミラー' in product_name or 'mirror' in product_name_lower or
    'card' in product_sku_lower or 'mirror' in product_sku_lower
)
is_hard_case = 'ハードケース' in product_name

if is_amazon_notebook and not is_hard_case:
    return '手帳型ケース'
```

## 残りの開発タスク

1. **PDF生成機能修復** - WeasyPrint システム依存関係の解決
2. **AI判定の動作確認** - 実データでのテスト実施
