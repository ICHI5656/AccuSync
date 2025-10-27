# 03. アーキテクチャ

- クライアント: Next.js (SPA/SSRハイブリッド) + API呼び出し（OpenAPI準拠）
- API: FastAPI + Uvicorn + PostgreSQL (SQLAlchemy) + Redis（ジョブ/キャッシュ）
- バッチ: Celery（CSV取込・PDF生成を非同期化）
- ストレージ: S3互換にPDF/ロゴ/印影/エラーレポートを保存
- IaC: Docker Compose（開発）/ Terraform or CDK（本番は任意）

## データフロー（CSV取込）
1. CSVアップロード（フロント）→ `/imports` API
2. S3一時保存 → ImportJob生成（PENDING）
3. CeleryがCSVを検証→DBトランザクション→結果保存→ジョブ完了/失敗
4. エラーは行別レポート（CSV）を生成してS3に保存（DL可）

## データフロー（請求書）
1. 期間＋対象取引先を選択→仮プレビュー（集計）
2. 単価ルール評価→税計算→UIで明細編集（任意）
3. 確定→PDF生成→S3保存→`Invoice`レコード作成→監査ログ
