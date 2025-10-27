# 04. フロントエンド実装（Next.js + TS）

## 主要ページ
- **/login**: 認証
- **/dashboard**: サマリー（今月の受注・請求・未入金）
- **/imports**: CSV取込履歴・新規取込（ドラッグ&ドロップ）
- **/orders**: 受注一覧/詳細/編集
- **/customers**: 取引先管理（単価タブ含む）
- **/products**: 商品管理
- **/invoices**: 請求書一覧/生成/再発行/プレビュー
- **/settings/issuer-companies**: 発行会社管理
- **/settings/users**: ユーザー/ロール

## UI要件
- Tableはサーバページング + 列フィルタ
- CSVマッピングUI（列ドラッグ&ドロップ/プレビュー）
- 金額/税/端数の即時計算表示
- PDFプレビュー（埋め込み）
