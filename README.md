# AccuSync（あきゅシンク） - 請求書作成システム

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)

**多様なフォーマット（CSV/Excel/PDF/TXT/画像）から受注データを取り込み、AI判断機能で自動処理し、請求書・納品書PDFを生成するBtoB向け内製ツール**

## ✨ 主な特徴

### 🤖 AI駆動のデータ処理（調整可能）
- **ファイル形式自動判別**: CSV、Excel、PDF、TXT、画像を自動認識
- **非構造化データ抽出**: 手書きメモやPDFから注文情報を抽出
- **自動マッピング**: 列名を自動的にフィールドにマッピング
- **データ品質チェック**: 異常値検出・欠損値補完

### 📊 柔軟な単価管理
- 会社別・商品別の単価設定
- 期間・数量条件による単価ルール
- 優先度による複数ルールの管理

### 📄 美しい帳票出力
- **ソフトグリーン基調**の柔らかいデザイン
- 請求書・納品書のPDF自動生成
- インボイス制度対応（適格請求書登録番号）
- A4印刷最適化

### 🔒 セキュアな管理
- JWT認証
- ロールベースアクセス制御（admin/accountant/viewer）
- 完全な監査ログ

## 🏗️ アーキテクチャ

```
AccuSync/
├── frontend/          # Next.js 14 (App Router) + TypeScript + Tailwind
├── backend/           # FastAPI + Python 3.11
│   ├── app/
│   │   ├── ai/       # AI統合層（OpenAI/Claude対応）
│   │   ├── services/ # ビジネスロジック
│   │   ├── models/   # SQLAlchemy モデル
│   │   └── api/      # REST API エンドポイント
│   └── alembic/      # DBマイグレーション
├── templates/         # 請求書・納品書HTMLテンプレート
├── testdata/          # テストデータ
├── config/            # AI設定ファイル
└── docker-compose.yml
```

### 技術スタック

**Backend**
- FastAPI + Uvicorn
- PostgreSQL + SQLAlchemy
- Redis + Celery（非同期処理）
- OpenAI GPT-4o / Anthropic Claude（AI機能）
- WeasyPrint（PDF生成）

**Frontend**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query

**Infrastructure**
- Docker + Docker Compose
- MinIO（S3互換ストレージ）
- PostgreSQL 16
- Redis 7

## 🚀 クイックスタート

### 前提条件

- Docker & Docker Compose
- （オプション）OpenAI API Key または Anthropic API Key

### 起動スクリプトで簡単起動！

```bash
# プロジェクトディレクトリに移動
cd /home/local-quest/claude-projects/AccuSync

# 起動スクリプトを実行（推奨）
./RUN.sh
```

または手動起動：

```bash
# 1. Docker起動
docker-compose up -d --build

# 2. データベースマイグレーション（初回のみ）
docker-compose exec api alembic revision --autogenerate -m "Initial"
docker-compose exec api alembic upgrade head
```

### アクセスURL（ポート競合回避済み）

| サービス | URL | 説明 |
|---------|-----|------|
| **Frontend** | http://localhost:3100 | メインUI |
| **Backend API** | http://localhost:8100 | REST API |
| **API Docs** | http://localhost:8100/docs | Swagger UI |
| **MinIO Console** | http://localhost:9101 | ストレージ管理 |

すべてのポートが標準ポートと競合しないように調整されています。

### AI機能の有効化（オプション）

`.env` ファイルを編集：

```env
# OpenAI を使用する場合
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here

# または Claude を使用する場合
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-claude-key-here
```

詳細は **START_HERE.md** と **DOCKER_GUIDE.md** を参照してください。

## 📖 使い方

### 1. ファイルアップロード

1. フロントエンドの「データ取り込み」ページにアクセス
2. CSV/Excel/PDF/TXT/画像ファイルをドラッグ&ドロップ
3. AI が自動的にファイル形式を判別し、データを抽出

### 2. データ確認・編集

1. 抽出されたデータをプレビュー
2. 必要に応じて手動で修正
3. 「インポート」ボタンでデータベースに保存

### 3. 請求書生成

1. 「請求書」ページにアクセス
2. 期間と取引先を選択
3. プレビューで明細を確認
4. 「PDF生成」でダウンロード

## ⚙️ AI機能の調整

AI機能は `config/ai_settings.yaml` で柔軟に調整できます：

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
    provider: openai
    confidence_threshold: 0.85

  auto_mapping:
    enabled: true

  data_quality_check:
    enabled: true

# コスト制御
cost_control:
  monthly_budget: 100.0  # USD
  usage_alerts:
    enabled: true
```

詳細は [AI設定ガイド](./config/ai_settings.yaml) を参照してください。

## 🔧 開発

### バックエンド開発

```bash
cd backend

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバーの起動
uvicorn app.main:app --reload
```

### フロントエンド開発

```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

### データベースマイグレーション

```bash
cd backend

# マイグレーションファイルの作成
alembic revision --autogenerate -m "description"

# マイグレーションの適用
alembic upgrade head

# ロールバック
alembic downgrade -1
```

## 📝 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🤝 コントリビューション

プルリクエストを歓迎します！大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📧 サポート

質問やバグ報告は [Issues](https://github.com/yourusername/AccuSync/issues) までお願いします。

---

**AccuSync（あきゅシンク）** - AI駆動の次世代請求書作成システム 🚀
