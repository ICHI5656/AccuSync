# 09. テスト / デバッグ

- 単体: pytest（サービス層・価格決定・税計算・CSVバリデーション）
- 結合: Testcontainers + PostgreSQL + MinIO（S3互換）
- E2E: Playwright（CSVアップ→請求書PDFまで）
- フィクスチャ: ダミー会社/商品/価格ルール/受注CSV
- デバッグ: 構成可能なアプリロガー（構造化JSON）+ リクエストID
