# 07. CSV仕様 & マッピング

## 入力CSV（例）
- 必須列: `order_no, order_date, customer_code, sku, qty`
- 任意列: `unit_price, product_name, customer_name, memo`

### サンプル行
```
10001,2025-09-30,CSTM001,SKU-ABC,5,1200,フルカバーガラス,C社メモ
```

## マッピングUI
- アップロード後、**列→フィールド**のドラッグ&ドロップ
- 事前保存した**テンプレート**を再利用可
- プレビューでエラー表示（型/必須）

## 取込ルール
- 同一 `order_no + customer` は**重複拒否**（設定で上書きモードも可）
- `unit_price` が空なら PricingService で決定
- 失敗行はエラーレポートCSVとしてS3保存
