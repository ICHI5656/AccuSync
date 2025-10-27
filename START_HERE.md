# 🚀 AccuSync クイックスタートガイド

**AccuSync（あきゅシンク）** - AI駆動の次世代請求書作成システムへようこそ！

## ✅ 完全にDocker対応済み

すべてのサービスがDockerコンテナで動作し、ポート競合を回避した設定になっています。

## 📝 起動手順（3ステップ）

### ステップ1: AI APIキーを設定（オプション）

`.env` ファイルを編集：

```bash
nano .env
```

以下のどちらかを設定：

```env
# OpenAI を使用する場合
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key-here

# または Claude を使用する場合
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-claude-api-key-here
```

**注**: APIキーがなくてもシステムは起動します。AI機能のみ無効になります。

### ステップ2: Docker起動

```bash
docker-compose up -d --build
```

初回起動は3-5分かかります。コーヒーでもどうぞ ☕

### ステップ3: データベース初期化

```bash
# マイグレーション実行（初回のみ）
docker-compose exec api alembic revision --autogenerate -m "Initial"
docker-compose exec api alembic upgrade head
```

## 🌐 アクセスURL

起動完了後、以下のURLにアクセスできます：

| サービス | URL | 説明 |
|---------|-----|------|
| **フロントエンド** | http://localhost:3100 | メインUI |
| **API ドキュメント** | http://localhost:8100/docs | Swagger UI |
| **ヘルスチェック** | http://localhost:8100/health | API状態確認 |
| **MinIO Console** | http://localhost:9101 | ストレージ管理 |

## 🎯 動作確認

### 1. ヘルスチェック

```bash
curl http://localhost:8100/health
```

期待される結果：
```json
{"status":"healthy","app":"AccuSync","version":"0.1.0"}
```

### 2. フロントエンドアクセス

ブラウザで http://localhost:3100 を開く

✅ ソフトグリーン基調の美しいホーム画面が表示されます

### 3. API ドキュメント

ブラウザで http://localhost:8100/docs を開く

✅ Swagger UIでAPIエンドポイントが確認できます

## 📊 ポート一覧（競合回避済み）

```
Frontend:     localhost:3100  (内部: 3000)
Backend API:  localhost:8100  (内部: 8000)
PostgreSQL:   localhost:5433  (内部: 5432)
Redis:        localhost:6380  (内部: 6379)
MinIO:        localhost:9100  (内部: 9000)
MinIO Console:localhost:9101  (内部: 9001)
```

すべてのポートが標準ポート（3000, 5432, 6379, 8000, 9000）と競合しないように設定されています。

## 🛠️ 基本コマンド

### ログ確認
```bash
# 全サービス
docker-compose logs -f

# 特定サービス
docker-compose logs -f api
docker-compose logs -f frontend
```

### コンテナ状態確認
```bash
docker-compose ps
```

### 停止・再起動
```bash
# 停止
docker-compose down

# 再起動
docker-compose restart

# 完全リセット（データ削除）
docker-compose down -v
```

## 🎨 デザインカラー

AccuSyncは事務員の方も安心して使える、柔らかいデザインです：

- **メインカラー**: ソフトグリーン `#6bb89c`
- **テキスト**: ダークグレー `#203036`
- **背景**: 白 `#ffffff`
- **罫線**: 淡いグリーン `#e7efea`

## 📚 ドキュメント

- **DOCKER_GUIDE.md**: 詳細なDocker操作ガイド
- **README.md**: プロジェクト概要
- **SETUP.md**: 開発セットアップ
- **PROGRESS.md**: 実装進捗レポート

## 🎯 現在使える機能

✅ **基盤システム**
- PostgreSQL データベース（11テーブル）
- Redis キャッシュ
- MinIO ストレージ
- FastAPI バックエンド
- Next.js フロントエンド
- Celery 非同期処理

✅ **AI統合層**
- OpenAI GPT-4o サポート
- Anthropic Claude サポート
- 柔軟な設定（config/ai_settings.yaml）

✅ **PDF生成**
- 請求書テンプレート（ソフトグリーン基調）
- 納品書テンプレート
- WeasyPrint PDF生成エンジン

✅ **ビジネスロジック**
- 会社別単価決定アルゴリズム
- 税計算・端数処理

## 🚧 次に実装予定

- ファイルパーサー（CSV/Excel/PDF/TXT/画像）
- データ取り込みAPI
- ファイルアップロード画面
- マスタ管理画面
- 請求書生成フロー

## 💡 トラブルシューティング

### コンテナが起動しない
```bash
docker-compose down
docker-compose up -d --build
docker-compose logs -f
```

### ポート競合エラー
すべてのポートは競合回避済みですが、念のため確認：
```bash
sudo lsof -i :3100
sudo lsof -i :8100
```

### データベースエラー
```bash
docker-compose restart db
docker-compose exec db psql -U accusync -d accusync
```

## 🎉 セットアップ完了！

これで AccuSync の完全な開発環境が整いました。

次は：
1. テストデータをアップロード（`testdata/` フォルダー）
2. AI APIキーを設定して機能を有効化
3. フロントエンド画面で実際に操作

**質問や問題があれば、Issuesまでお気軽に！**

---

Made with ❤️ by AccuSync Team
