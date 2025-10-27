# AccuSync Docker 起動ガイド

## 📌 ポート構成（競合回避済み）

| サービス | 内部ポート | 外部ポート | URL |
|---------|-----------|-----------|-----|
| **Frontend** | 3000 | **3100** | http://localhost:3100 |
| **Backend API** | 8000 | **8100** | http://localhost:8100 |
| **PostgreSQL** | 5432 | **5433** | localhost:5433 |
| **Redis** | 6379 | **6380** | localhost:6380 |
| **MinIO** | 9000 | **9100** | http://localhost:9100 |
| **MinIO Console** | 9001 | **9101** | http://localhost:9101 |

すべてのポートが標準ポートと競合しないように調整されています。

## 🚀 起動手順

### 1. AI APIキーの設定（オプション）

`.env` ファイルを編集してAPIキーを設定します：

```bash
# OpenAI を使用する場合
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here

# または Claude を使用する場合
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-claude-api-key-here
```

**注意**: APIキーを設定しない場合、AI機能は無効になりますが、システムは起動します。

### 2. Docker コンテナの起動

```bash
# プロジェクトディレクトリに移動
cd /home/local-quest/claude-projects/AccuSync

# コンテナをビルド＆起動
docker-compose up -d --build
```

初回起動時は、イメージのダウンロードとビルドに数分かかります。

### 3. ログの確認

```bash
# 全サービスのログを表示
docker-compose logs -f

# 特定サービスのログのみ表示
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f celery_worker
```

### 4. コンテナの状態確認

```bash
docker-compose ps
```

すべてのサービスが `Up` 状態になっていることを確認してください：

```
NAME                    STATUS
accusync-api            Up
accusync-celery-worker  Up
accusync-db             Up (healthy)
accusync-frontend       Up
accusync-minio          Up (healthy)
accusync-redis          Up (healthy)
```

### 5. データベースマイグレーション

初回起動時のみ実行：

```bash
# マイグレーションファイルの生成
docker-compose exec api alembic revision --autogenerate -m "Initial migration"

# マイグレーションの適用
docker-compose exec api alembic upgrade head
```

## 🌐 アクセス

### Frontend（Next.js）
- **URL**: http://localhost:3100
- **説明**: ユーザーインターフェース

### Backend API
- **URL**: http://localhost:8100
- **API Docs**: http://localhost:8100/docs
- **Health Check**: http://localhost:8100/health

動作確認：
```bash
curl http://localhost:8100/health
# → {"status":"healthy","app":"AccuSync","version":"0.1.0"}
```

### MinIO Console（ストレージ管理）
- **URL**: http://localhost:9101
- **ユーザー名**: minioadmin
- **パスワード**: minioadmin

### PostgreSQL（データベース接続）
```bash
# コンテナ内から接続
docker-compose exec db psql -U accusync -d accusync

# ホストから接続（psqlがインストールされている場合）
psql -h localhost -p 5433 -U accusync -d accusync
```

## 🛠️ 開発コマンド

### コンテナの停止

```bash
# すべてのコンテナを停止
docker-compose down

# ボリュームも削除（データベースをリセット）
docker-compose down -v
```

### コンテナの再起動

```bash
# すべて再起動
docker-compose restart

# 特定のサービスのみ再起動
docker-compose restart api
docker-compose restart frontend
```

### コンテナに入る

```bash
# Backend（Python）
docker-compose exec api bash

# Frontend（Node.js）
docker-compose exec frontend sh

# PostgreSQL
docker-compose exec db bash
```

### ログのクリア

```bash
docker-compose down
docker system prune -f
docker-compose up -d
```

## 🧪 動作テスト

### 1. Backend APIの動作確認

```bash
# ヘルスチェック
curl http://localhost:8100/health

# OpenAPI仕様の取得
curl http://localhost:8100/openapi.json
```

### 2. Frontend の動作確認

ブラウザで http://localhost:3100 を開いて、AccuSyncのホーム画面が表示されることを確認。

### 3. データベース接続確認

```bash
docker-compose exec api python -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection: OK')
"
```

### 4. Redis接続確認

```bash
docker-compose exec redis redis-cli ping
# → PONG
```

### 5. MinIO接続確認

```bash
curl http://localhost:9100/minio/health/live
# → OK
```

## ⚠️ トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
docker-compose logs api
docker-compose logs frontend

# ポート競合の確認
sudo lsof -i :3100
sudo lsof -i :8100
```

### データベース接続エラー

```bash
# データベースの状態を確認
docker-compose ps db

# ヘルスチェックが失敗している場合
docker-compose restart db
docker-compose logs db
```

### フロントエンドがビルドできない

```bash
# node_modules を削除して再ビルド
docker-compose down
docker-compose up -d --build frontend
```

### ボリュームをリセット

```bash
# すべてのデータを削除して最初からやり直す
docker-compose down -v
docker volume prune -f
docker-compose up -d --build
```

## 🔄 開発ワークフロー

### バックエンドの変更

1. `backend/` 内のファイルを編集
2. 変更は自動的にリロード（uvicorn --reload）
3. ブラウザで http://localhost:8100/docs を更新

### フロントエンドの変更

1. `frontend/` 内のファイルを編集
2. 変更は自動的にリロード（Next.js Fast Refresh）
3. ブラウザで http://localhost:3100 を更新

### データベーススキーマの変更

1. `backend/app/models/` でモデルを編集
2. マイグレーションファイルを生成：
   ```bash
   docker-compose exec api alembic revision --autogenerate -m "変更内容"
   ```
3. マイグレーションを適用：
   ```bash
   docker-compose exec api alembic upgrade head
   ```

## 📊 リソース使用状況

```bash
# コンテナのリソース使用状況を確認
docker stats

# ディスク使用量を確認
docker system df
```

## 🎯 次のステップ

1. **AI機能を有効化**: `.env` にAPIキーを設定
2. **テストデータのインポート**: `testdata/` のファイルを使用
3. **フロントエンドの実装**: ファイルアップロード画面から開始

---

**完璧に動作する環境が整いました！** 🎉
