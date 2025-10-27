# 請求書作成システム — AI実装指示書（2025-10-23）

この `docs/` は、AI（および開発者）が**そのまま実装に移せる**よう設計された実装指示書です。  
仕様は **フロント**・**バックエンド**・**データモデル**・**セキュリティ**・**CSV/手動入力**・**請求書PDF生成**・**テスト/デバッグ**・**デプロイ** の観点で分割されています。

最小要件：
- CSVで受け取った**商品注文**をDBに取り込み、**取引先（顧客会社）ごと**に注文数/金額を集計
- **会社別の単価**（商品×会社）を設定可能
- **請求書発行会社**（自社アカウント）を**複数登録**可能（ヘッダー情報・振込先・印影など）
- CSV以外でも**手動入力**で受注登録/編集可能
- 受領データ（CSVの全情報）は**DBで完全管理**（監査ログ含む）
- **請求書をPDFで生成**し、履歴/再発行管理
- 税計算（日本の消費税 10% をデフォルト。品目/顧客別税率可）

推奨スタック（変更可）:
- フロント: Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + TanStack Query
- バック: FastAPI (Python) もしくは NestJS (TypeScript) ※本書は FastAPI 例示
- DB: PostgreSQL (+ SQLAlchemy / Alembic)
- 認証: OAuth 2.1 / OpenID Connect（Auth0等） or 自前（JWT）
- ストレージ: S3互換（PDF/印影）
- インフラ: Docker Compose（ローカル）/ AWS（本番）

次へ：
- 全体像: `00_overview.md`
- 機能要件: `01_requirements.md`
- データモデル: `02_data_model.md`
- アーキテクチャ: `03_architecture.md`
- フロント実装: `04_frontend.md`
- バックエンド実装: `05_backend.md`
- セキュリティ: `06_security.md`
- CSV仕様: `07_csv_spec.md`
- 請求書生成: `08_invoice_generation.md`
- テスト/デバッグ: `09_testing_debugging.md`
- デプロイ: `10_deployment.md`
- API仕様（エンドポイント）: `11_api_spec.md`
- 権限/ロール: `12_user_roles_permissions.md`
- マイグレーション/初期データ: `13_migration_seeding.md`
- **AI機能実装: `14_ai_features.md` (NEW - 2025-10-24追加)**
