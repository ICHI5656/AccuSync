# AccuSync 使い方ガイド

## 起動方法

```bash
cd /home/local-quest/claude-projects/AccuSync
./RUN.sh
```

または

```bash
docker-compose up -d --build
```

## アクセスURL

| サービス | URL | 説明 |
|---------|-----|------|
| **フロントエンド** | http://localhost:3100 | メインUI |
| **データ取り込み** | http://localhost:3100/imports | ファイルアップロード画面 |
| **ジョブ一覧** | http://localhost:3100/jobs | インポートジョブ管理 |
| **API ドキュメント** | http://localhost:8100/docs | Swagger UI |
| **MinIO Console** | http://localhost:9101 | ストレージ管理 |

## 使い方

### 1. データ取り込み（ファイルアップロード）

1. **http://localhost:3100/imports** にアクセス
2. ファイルをドラッグ&ドロップ（またはクリックして選択）
   - 対応形式: CSV, Excel (.xlsx/.xls), PDF, TXT
3. 「アップロード」ボタンをクリック
4. （オプション）「プレビュー」で内容確認
5. 「インポート実行」でAI処理開始
   - AI自動マッピング
   - データ品質チェック
   - エンコーディング自動検出

### 2. ジョブ管理とデータベース保存

1. **http://localhost:3100/jobs** にアクセス
2. 処理状況を確認
   - 待機中、処理中、完了、失敗
3. 完了したジョブの「DBに保存」ボタンをクリック
   - 顧客データ自動作成
   - 商品データ自動作成
   - 注文データ保存

### 3. データの流れ

```
ファイルアップロード
    ↓
AI処理（自動マッピング・品質チェック）
    ↓
プレビュー確認（オプション）
    ↓
インポートジョブ作成
    ↓
バックグラウンド処理（Celery）
    ↓
完了後、DBに保存
    ↓
顧客・商品・注文データ蓄積
```

## テストデータ

`testdata/` フォルダーに実際のサンプルファイルがあります：

| ファイル | 形式 | 内容 |
|---------|------|------|
| 2025-10-17注文書.csv | CSV (Shift-JIS) | 注文データ |
| 251010株式会社Quest様注文書.xlsx | Excel | 注文書 |
| クエスト発注書2024.2.29.pdf | PDF | 発注書 |
| 青江注文.txt | テキスト | 手書きメモ風注文 |

## AI機能

### 自動機能

1. **ファイル形式検出**: 拡張子とchardetで自動判別
2. **エンコーディング検出**: UTF-8/Shift-JIS/CP932等に自動対応
3. **列名マッピング**: ファイルの列名→システムフィールドへ自動変換
4. **データ品質チェック**: 異常値・欠損値を警告
5. **非構造化データ抽出**: PDFやテキストから情報抽出

### 設定調整

`config/ai_settings.yaml` で機能のON/OFF、信頼度閾値等を調整可能

```yaml
features:
  file_format_detection:
    enabled: true
    confidence_threshold: 0.8
  data_extraction:
    enabled: true
    confidence_threshold: 0.85
```

## トラブルシューティング

### ファイルアップロードが失敗する

- 対応形式を確認（CSV, Excel, PDF, TXT のみ）
- ファイルサイズを確認（大きすぎないか）
- コンソールのエラーメッセージを確認

### ジョブが「処理中」のまま

- Celery Workerの状態確認：
  ```bash
  docker-compose logs celery_worker
  ```
- API のログ確認：
  ```bash
  docker-compose logs api
  ```

### プレビューでデータが表示されない

- エンコーディング問題の可能性
- ファイル形式が正しいか確認
- ジョブ一覧で警告・エラーメッセージを確認

### DBに保存できない

- ジョブが「完了」状態か確認
- 必須フィールド（顧客名、商品名）があるか確認
- PostgreSQL の状態確認：
  ```bash
  docker-compose ps db
  ```

## データベース確認

保存されたデータを確認：

```bash
# PostgreSQLに接続
docker-compose exec db psql -U accusync -d accusync

# テーブル確認
\dt

# 顧客データ確認
SELECT * FROM customer_companies LIMIT 5;

# 商品データ確認
SELECT * FROM products LIMIT 5;

# 注文データ確認
SELECT * FROM orders ORDER BY created_at DESC LIMIT 5;
```

## API直接利用

### ファイルアップロード

```bash
curl -X POST http://localhost:8100/api/v1/imports/upload \
  -F "file=@testdata/2025-10-17注文書.csv"
```

### プレビュー

```bash
curl -X POST http://localhost:8100/api/v1/imports/preview \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "xxx",
    "filename": "2025-10-17注文書.csv",
    "file_type": "csv",
    "preview_rows": 10
  }'
```

### ジョブ作成

```bash
curl -X POST http://localhost:8100/api/v1/imports/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "xxx",
    "filename": "2025-10-17注文書.csv",
    "file_type": "csv",
    "apply_ai_mapping": true,
    "apply_quality_check": true
  }'
```

## 次のステップ

1. テストデータでシステムを試す
2. 実際のデータファイルでテスト
3. マスタデータ（発行会社、取引先、商品）を整備
4. 請求書生成機能を実装（Phase 4）

---

**AccuSync - AI駆動の請求書作成システム** 🚀
