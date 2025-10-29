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
- **デバイス自動検出**: 商品名から機種情報（iPhone, Galaxy, AQUOS等）を自動抽出

### 📊 在庫管理用の統計システム
- **5つの専用ページ**: 総計、件数統計、個数統計、件数サマリー、個数サマリー
- **ハードケース統計**: 機種別（AQUOS wish4, iPhone 15 Pro等）の件数・個数集計
- **手帳ケース統計**: 種類別（キャメル、coloer、薄いタイプ等）にサイズ・機種で詳細集計
- **インタラクティブUI**: サイドバーで機種別・サイズ別の詳細をクリック展開
- **件数vs個数の分離**: 注文件数と商品個数を明確に区別して表示

### 💰 柔軟な単価管理
- **価格マトリクス**: グリッド形式で会社別×商品タイプ別の卸単価を一括管理
- 会社別・商品別の単価設定
- 商品タイプキーワードによる価格ルール（デザイン名を除外）
- 期間・数量条件による単価ルール
- 3段階の価格適用優先順位（価格マトリクス > 商品マスタ > CSV）

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

### 主要な画面

| 画面 | URL | 機能 |
|-----|-----|------|
| ホーム | http://localhost:3100 | ダッシュボード・クイックアクセス |
| データ取り込み | http://localhost:3100/imports | CSV/Excel/PDFインポート |
| ジョブ一覧 | http://localhost:3100/jobs | インポートジョブ管理 |
| 商品管理 | http://localhost:3100/products | 商品マスタ・価格設定 |
| **価格マトリクス** | http://localhost:3100/pricing-matrix | **会社別卸単価設定** |
| 顧客管理 | http://localhost:3100/customers | 取引先情報・締め日・支払い日 |
| 注文一覧 | http://localhost:3100/orders | 取り込んだ注文データ表示 |
| **📊 注文統計** | http://localhost:3100/stats | **在庫管理用の詳細統計** |
| システム設定 | http://localhost:3100/settings | AI設定・請求者情報・DB統計 |

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

### 1. 商品・顧客の事前登録

1. **商品マスタ登録**: 「商品管理」ページで商品を事前登録
   - SKU、商品名、標準単価、税率を設定
2. **顧客情報登録**: 「顧客管理」ページで取引先を登録
   - 会社名、締め日、支払い日を設定

### 2. 価格マトリクスの設定（オプション）

1. 「価格マトリクス」ページにアクセス
2. 商品タイプ（行）× 取引先（列）のグリッドで価格を入力
3. 各セルの「保存」ボタンで確定
4. 設定した価格は**インポート時に最優先で適用**されます

### 3. ファイルアップロード

1. フロントエンドの「データ取り込み」ページにアクセス
2. CSV/Excel/PDF/TXT/画像ファイルをドラッグ&ドロップ
3. AI が自動的にファイル形式を判別し、データを抽出

### 4. データ確認・編集

1. 抽出されたデータをプレビュー（必須フィールドのみ表示）
2. 列マッピングで自動マッピングを確認
3. 必要に応じて手動で修正
4. 「インポート」ボタンでデータベースに保存

### 5. 注文データの確認

1. 「注文一覧」ページで取り込んだデータを確認
2. 期間や取引先でフィルタリング
3. 集計データを表示

### 6. 請求書生成（今後実装予定）

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

## ✅ 実装済み機能

### データ取り込み
- ✅ ファイルアップロード（CSV/Excel/PDF/TXT）
- ✅ AI自動ファイル形式判別
- ✅ AI自動データ抽出
- ✅ 列マッピング（自動・手動）
- ✅ プレビュー表示（必須フィールドのみ）
- ✅ データ品質チェック
- ✅ バックグラウンドジョブ処理（Celery）

### マスタデータ管理
- ✅ 商品マスタ管理（CRUD）
- ✅ 顧客管理（CRUD）
- ✅ 締め日・支払い日設定
- ✅ 顧客識別子による自動検出
- ✅ AI顧客タイプ判定（法人/個人）

### 価格管理
- ✅ **価格マトリクス**（グリッド形式UI）
- ✅ 会社別×商品タイプ別の卸単価設定
- ✅ 商品タイプキーワードによる価格ルール
- ✅ 3段階の価格適用優先順位
- ✅ 期間・数量条件による価格ルール

### 注文管理
- ✅ 注文データ蓄積
- ✅ 注文一覧表示
- ✅ 期間・取引先フィルタリング
- ✅ 集計データ表示

### 📊 統計・分析機能
- ✅ **5つの独立した統計ページ**（在庫管理用）
  - 総計ページ（全体サマリー）
  - 件数統計（注文件数の詳細）
  - 個数統計（商品個数の詳細）
  - 件数サマリー（件数概要とトップ5）
  - 個数サマリー（個数概要とトップ5）
- ✅ **ハードケース統計**: 機種別の件数・個数集計
- ✅ **手帳ケース統計**: 種類別（キャメル、coloer等）にサイズ・機種で集計
- ✅ **インタラクティブなサイドバー**: クリックで機種別・サイズ別の詳細展開
- ✅ **デバイス自動検出**: 商品名から機種情報を自動抽出
- ✅ **件数と個数の明確な分離**: 注文件数と商品個数を別々に表示

### システム機能
- ✅ Docker環境構築
- ✅ データベースマイグレーション
- ✅ API認証（JWT）
- ✅ Swagger API ドキュメント

### 今後実装予定
- ⏳ 請求書PDF生成
- ⏳ 納品書PDF生成
- ⏳ インボイス制度対応
- ⏳ メール送信機能

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

質問やバグ報告は [Issues](https://github.com/ICHI5656/AccuSync/issues) までお願いします。

---

**AccuSync（あきゅシンク）** - AI駆動の次世代請求書作成システム 🚀
