
# あきゅシンク — 請求書・納品書テンプレ（柔らかい印象・ロゴなし）

- 形式: HTML + CSS（A4印刷対応／@page指定）
- スタイル: ソフトグリーン基調、丸み・余白重視、BtoBで親しみやすい雰囲気
- ロゴ非使用（社名のみテキスト表示）
- 日本語フォントは環境依存。印刷時は PDF 変換推奨。

## ファイル
- `invoice.html` — 御請求書
- `delivery_note.html` — 納品書
- `style.css` — 共通スタイル

## 差し込みプレースホルダ
テンプレートは Handlebars 風 `{placeholder}` 記法を使用:
- 例）`{issuer.name}`, `{customer.name}`, `{period_start}`, `{#each items} ... {/each}`

## 使い方（例：Node/PuppeteerでPDF化）
1) 変数を差し込んだ HTML を生成  
2) `window.print()` または Puppeteer で PDF 出力（A4, margin 18mm）

## 備考
- インボイス制度の登録番号欄（`{issuer.tax_id}`）を請求書に用意
- 金額は税抜/税込の両方を表で表示
- 余白・角丸・淡色ヘッダーで優しい印象を演出
