# 05. バックエンド実装（FastAPI例）

## サービス
- **PricingService**: 会社×商品×数量×期間で最適単価を返す
- **ImportService**: CSV検証・マッピング適用・重複チェック・トランザクション保存
- **InvoiceService**: 明細集計→税計算→PDF生成→保存→状態遷移
- **AuditService**: 変更差分の記録（Before/After）
- **FileService**: S3入出力、署名URL生成

## 単価決定アルゴリズム（擬似コード）
```
rules = get_rules(customer_id, product_id, date_in_period)
candidates = filter_by_qty(rules, qty)
sort by priority desc, start_date desc
price = candidates.first?.price or product.default_price
```

## 端数処理
- 設定: `ROUND_DOWN | ROUND_UP | ROUND_HALF_UP`（円）
- 適用単位: 行単位→小計→税→合計 の順で丸め
