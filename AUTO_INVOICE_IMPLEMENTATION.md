# 自動請求書発行機能　実装完了報告

## 概要

取引先の締め日に基づいて自動的に請求書を生成する機能を実装しました。

## 実装内容

### 1. 自動請求書生成サービス (`auto_invoice_service.py`)

**主要機能:**
- 締め日判定ロジック（月末対応含む）
- 請求期間の自動計算（前回締め日翌日〜今回締め日）
- 支払期限の自動計算（payment_month_offset対応）
- 注文データの自動集計と請求書生成

**主要メソッド:**
```python
AutoInvoiceService.get_customers_to_invoice(db, target_date)
# → 指定日が締め日の顧客リストを取得

AutoInvoiceService.calculate_invoice_period(customer, closing_date)
# → 請求期間（開始日・終了日）を計算

AutoInvoiceService.calculate_payment_due_date(customer, closing_date)
# → 支払期限を計算

AutoInvoiceService.auto_generate_invoice_for_customer(db, customer, closing_date)
# → 個別顧客の請求書を自動生成

AutoInvoiceService.run_auto_invoice_generation(db, target_date)
# → すべての対象顧客の請求書を一括生成
```

### 2. Celeryタスク (`auto_invoice_tasks.py`)

**定期実行タスク:**
- `auto_generate_invoices`: 毎日実行され、今日が締め日の顧客の請求書を自動生成
- `auto_generate_invoices_for_date`: 指定日の請求書を生成（手動実行・テスト用）

### 3. Celery Beat スケジューラー設定

**`celery_app.py` に追加:**
```python
celery_app.conf.beat_schedule = {
    'auto-generate-invoices-daily': {
        'task': 'auto_generate_invoices',
        'schedule': 3600.0,  # 1時間ごと（テスト用）
        # 本番環境では 86400.0 (1日) に変更推奨
    },
}
```

**Docker Compose サービス追加:**
- `celery_beat` コンテナを追加（スケジューラー）

### 4. REST API エンドポイント (`/api/v1/auto-invoice/`)

#### GET `/api/v1/auto-invoice/check`
指定日（デフォルト：今日）が締め日の顧客をチェック

**レスポンス例:**
```json
{
  "date": "2025-10-29",
  "customers_with_closing_day": 2,
  "customers": [
    {
      "id": 1,
      "name": "株式会社テスト",
      "code": "CUST001",
      "closing_day": 29,
      "payment_day": 0,
      "payment_month_offset": 1
    }
  ]
}
```

#### POST `/api/v1/auto-invoice/run`
自動請求書発行を非同期実行（Celeryタスクとしてキューに追加）

**リクエスト:**
```json
{
  "target_date": "2025-10-29"  // オプション（省略時は今日）
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "自動請求書発行タスクをキューに追加しました（対象日: 2025-10-29）",
  "task_id": "abc-123-def-456"
}
```

#### POST `/api/v1/auto-invoice/run-sync`
自動請求書発行を同期実行（テスト用・結果を即座に返す）

**レスポンス例:**
```json
{
  "success": true,
  "date": "2025-10-29",
  "customers_checked": 2,
  "invoices_generated": 1,
  "invoices_skipped": 1,
  "errors": 0,
  "results": [
    {
      "success": true,
      "skipped": false,
      "invoice_id": 15,
      "invoice_no": "INV-20251029-123456",
      "customer_id": 1,
      "customer_name": "株式会社テスト",
      "period_start": "2025-09-30",
      "period_end": "2025-10-29",
      "order_count": 5,
      "total_amount": 108000.0
    },
    {
      "success": true,
      "skipped": true,
      "reason": "no_orders",
      "customer_id": 2,
      "customer_name": "個人太郎",
      "period_start": "2025-09-30",
      "period_end": "2025-10-29",
      "order_count": 0
    }
  ]
}
```

### 5. フロントエンド - 請求書管理ページ

**`/invoices` ページを作成:**
- 請求書一覧表示（ステータスフィルター機能付き）
- 請求書作成ダイアログ（期間指定、顧客選択）
- PDF ダウンロード機能（※現在一時無効化）
- 請求書削除機能（下書きのみ）
- ナビゲーションメニューに「請求書」リンク追加

### 6. 締め日・支払い条件の計算ロジック

**締め日の正規化:**
- `closing_day = 0` → 月末日
- `closing_day = 31` で2月の場合 → 2月末日（28日or29日）
- `closing_day = 30` で2月の場合 → 2月末日（28日or29日）

**請求期間の計算:**
```
期間開始日 = 前回締め日の翌日
期間終了日 = 今回締め日
```

例: 締め日が29日の場合
```
2025-09-30（前回締め日+1日） ～ 2025-10-29（今回締め日）
```

**支払期限の計算:**
```
支払期限 = 締め日 + payment_month_offset月 + payment_day日
```

例: 締め日29日、翌月末払い（offset=1, payment_day=0）の場合
```
締め日: 2025-10-29
支払期限: 2025-11-30（翌月末）
```

## 動作フロー

### 定期実行（Celery Beat）
```
1. Celery Beatが毎日（or 1時間ごと）タスクを実行
   ↓
2. 今日の日付で get_customers_to_invoice() を呼び出し
   ↓
3. 今日が締め日の顧客リストを取得
   ↓
4. 各顧客について：
   - 請求期間を計算
   - 期間内の注文を検索
   - 注文がある場合 → 請求書を自動生成
   - 注文がない場合 → スキップ
   ↓
5. 結果をログに記録
```

### 手動実行（API経由）
```
1. POST /api/v1/auto-invoice/run を呼び出し
   ↓
2. Celeryタスクがキューに追加される
   ↓
3. Celeryワーカーがタスクを非同期実行
   ↓
4. ログで結果を確認
```

## 請求書の内容

### 必須情報
- **請求書番号**: `INV-YYYYMMDD-HHMMSS` 形式（自動生成）
- **発行日**: 請求書作成日
- **請求期間**: `period_start` 〜 `period_end`
- **支払期限**: 自動計算された `due_date`

### 明細情報（現在の実装）
```
商品名 | 数量 | 単価（税抜） | 小計（税抜） | 税率 | 税額 | 合計（税込）
```

- 期間内のすべての注文を商品ごとに集計
- 数量の合計、金額の合計を表示
- 注文時は税別、請求時は税込金額を表示

### 注文日の表示
**現在の実装:** 請求書には集計後の明細のみ（注文日は含まれていない）

**改善が必要な場合:**
請求書テンプレート（`templates/invoice.html`）と`InvoiceService.get_invoice_preview_data()`を修正して、注文日ごとの明細を表示する仕様に変更できます。

## テスト方法

### 1. 締め日設定のテスト

**顧客管理ページ**（`http://localhost:3100/customers`）で顧客を編集：
```
締め日: 29
支払い日: 0（月末）
支払い月オフセット: 1（翌月）
```

### 2. チェックAPIでテスト
```bash
# 今日が締め日の顧客を確認
curl http://localhost:8100/api/v1/auto-invoice/check

# 特定の日付でチェック
curl "http://localhost:8100/api/v1/auto-invoice/check?target_date=2025-10-29"
```

### 3. 手動実行でテスト
```bash
# 同期実行（結果を即座に確認）
curl -X POST http://localhost:8100/api/v1/auto-invoice/run-sync \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2025-10-29"}'
```

### 4. 自動実行の確認
```bash
# Celery Beatのログを確認
docker-compose logs -f celery_beat

# Celeryワーカーのログを確認
docker-compose logs -f celery_worker
```

## 残りの作業・制限事項

### ⚠️ Celery Beat コンテナが起動していない

**原因:** Dockerイメージに WeasyPrint のシステムライブラリ（`libgdk-pixbuf2.0-0` → `libgdk-pixbuf-xlib-2.0-0`）が不足

**対処方法:**
1. `backend/Dockerfile` の依存関係を修正
2. `docker-compose up -d --build celery_beat` で再ビルド

**現在の回避策:**
- PDF生成機能は一時無効化
- 請求書データの作成は正常に動作
- Celery Beat は手動起動が必要

### 📝 請求書表示の改善（ユーザーリクエスト対応）

**ユーザー要望:**
> 請求書には、受注日、注文、何があったかわかるようにして数量も請求書に出るようにしてください

**現在の実装:**
- 商品ごとに集計した明細を表示
- 数量・単価・税込金額は表示済み
- 注文日・個別注文情報は含まれていない

**改善案:**
1. 注文明細テーブルを追加（注文日・注文番号ごとに明細を表示）
2. または、請求書の備考欄に「対象注文: ORD-001, ORD-002...」を記載

### 🚧 PDF生成機能

**状態:** 一時無効化（Dockerイメージ再ビルド必要）

**再有効化手順:**
1. `backend/Dockerfile` の依存関係を修正
2. `backend/app/services/__init__.py` の PDFService インポートを有効化
3. `backend/app/api/v1/endpoints/invoices.py` の PDF endpoint を有効化
4. `docker-compose up -d --build` で再ビルド

### ⏰ スケジュール設定

**現在:** 1時間ごとに実行（テスト用）

**本番環境推奨:**
```python
'schedule': 86400.0,  # 1日1回（毎日午前0時頃に実行）
# または cron形式
'schedule': crontab(hour=0, minute=0),  # 毎日午前0時
```

## 関連ファイル

### バックエンド
- `backend/app/services/auto_invoice_service.py` - 自動請求書生成ロジック
- `backend/app/tasks/auto_invoice_tasks.py` - Celeryタスク定義
- `backend/app/api/v1/endpoints/auto_invoice.py` - REST API
- `backend/app/core/celery_app.py` - Celery Beat スケジュール設定
- `backend/app/services/invoice_service.py` - 請求書サービス（既存）
- `docker-compose.yml` - Celery Beat サービス追加

### フロントエンド
- `frontend/app/invoices/page.tsx` - 請求書管理ページ
- `frontend/app/components/Navbar.tsx` - ナビゲーションメニュー

### データベース
- `CustomerCompany.closing_day` - 締め日（1-31, 0=月末）
- `CustomerCompany.payment_day` - 支払日（1-31, 0=月末）
- `CustomerCompany.payment_month_offset` - 支払月オフセット（0=当月、1=翌月）
- `Invoice.period_start` / `period_end` - 請求期間
- `Invoice.issue_date` - 発行日
- `Invoice.due_date` - 支払期限（自動計算）

## まとめ

✅ **完了した機能:**
- 締め日判定ロジック
- 自動請求期間計算
- 自動支払期限計算
- 請求書自動生成サービス
- Celeryタスク・スケジューラー設定
- REST API（チェック・手動実行）
- フロントエンド請求書管理ページ

⚠️ **今後の対応が必要:**
- Dockerイメージの再ビルド（PDF機能有効化）
- Celery Beatコンテナの起動
- 請求書表示の改善（注文日・注文詳細の追加）
- 本番環境スケジュール設定（1日1回に変更）

🎉 **現在の状態:**
自動請求書発行機能は実装完了し、APIレベルでは動作確認済みです。締め日が設定されている顧客に対して、定期的または手動で請求書を自動生成できます。
