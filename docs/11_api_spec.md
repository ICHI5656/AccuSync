# 11. API仕様（REST）

ベースURL例: `/api/v1`

## 認証
- `POST /auth/login`（OIDCの場合は不要）
- `GET /me`

## マスタ
- `GET /issuer-companies` / `POST /issuer-companies`
- `GET /customers` / `POST /customers`
- `GET /products` / `POST /products`
- `GET /pricing-rules` / `POST /pricing-rules`

## 受注
- `GET /orders` / `POST /orders` / `GET /orders/{id}` / `PUT /orders/{id}`
- `POST /imports`（CSVアップロード）
- `GET /import-jobs` / `GET /import-jobs/{id}` / `GET /import-jobs/{id}/error-report`

## 請求
- `POST /invoices/preview`（期間/顧客で集計プレビュー）
- `POST /invoices`（確定生成）
- `GET /invoices` / `GET /invoices/{id}` / `POST /invoices/{id}/pdf`（再生成）
- `POST /invoices/{id}/void`（取消）

## 監査
- `GET /audit-logs`

各エンドポイントの詳細は実装時にOpenAPIで自動生成（FastAPI）。
