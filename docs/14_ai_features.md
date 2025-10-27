# AI機能実装ガイド

**最終更新: 2025-10-24**

## 概要

AccuSyncのAI機能は、データ処理を自動化・効率化するために設計されています。すべてのAI機能はオプションであり、`config/ai_settings.yaml`で個別に有効/無効を切り替えられます。

## アーキテクチャ

### プロバイダー抽象化

```python
AIProviderFactory
    ↓
AIProvider (抽象基底クラス)
    ├─ OpenAIProvider  # GPT-4o使用
    └─ ClaudeProvider  # Claude 3.5 Sonnet使用
```

すべてのプロバイダーは `app/ai/base.py` の `AIProvider` インターフェースを実装します。

### ファクトリーパターンの使用

```python
from app.ai.factory import AIProviderFactory

# 環境変数 AI_PROVIDER に基づいて適切なプロバイダーを返す
ai_provider = AIProviderFactory.create()

# または明示的に指定
ai_provider = AIProviderFactory.create(provider_name="openai")
ai_provider = AIProviderFactory.create(provider_name="claude")
```

## 実装済みAI機能

### 1. ファイル形式自動判別

**メソッド:** `detect_file_format()`

```python
result = await ai_provider.detect_file_format(
    file_content=file_bytes,
    file_name="document.dat",
    file_extension=".dat"
)

# result.file_type: "csv", "excel", "pdf", "txt", "image"
# result.confidence: 0.0 ~ 1.0
# result.metadata: 追加情報
```

**現在の実装:** 拡張子ベースの簡易判定（本格的なAI判定は未実装）

### 2. 非構造化データ抽出

**メソッド:** `extract_data()`

```python
result = await ai_provider.extract_data(
    content="テキストコンテンツ...",
    file_type="txt",
    extract_fields=["order_no", "customer_name", "product_name", "qty"]
)

# result.success: True/False
# result.data: [{"order_no": "001", "customer_name": "株式会社テスト", ...}]
# result.confidence: 0.0 ~ 1.0
# result.errors: エラーメッセージリスト
```

**使用例:** PDFや手書きメモから注文情報を抽出

### 3. 列名自動マッピング

**メソッド:** `auto_map_columns()`

```python
result = await ai_provider.auto_map_columns(
    column_names=["注文番号", "お客様名", "品名", "個数"],
    target_fields=["order_no", "customer_name", "product_name", "qty"],
    sample_data=[{...}]  # オプション
)

# result.success: True/False
# result.mapping: {"注文番号": "order_no", "お客様名": "customer_name", ...}
# result.confidence: 0.0 ~ 1.0
```

**使用ケース:** 様々なフォーマットのCSV/Excelファイルに対応

### 4. データ品質チェック

**メソッド:** `check_data_quality()`

```python
result = await ai_provider.check_data_quality(
    data=[{...}, {...}],
    rules={
        "required_fields": ["customer_name", "product_name"],
        "data_types": {"qty": "int", "unit_price": "float"}
    }
)

# result.success: True/False
# result.issues: 検出された問題のリスト
# result.suggestions: 修正提案
# result.enhanced_data: 補完後のデータ
```

**チェック内容:**
- 必須フィールドの欠損
- データ型の不一致
- 日付フォーマットの統一
- 数値フォーマットの統一
- 異常値の検出
- 重複データの検出

### 5. 顧客タイプ判定（法人/個人）

**メソッド:** `classify_customer_type()`

```python
result = await ai_provider.classify_customer_type(
    customer_name="株式会社テストコーポレーション",
    additional_info={
        "address": "東京都渋谷区...",
        "phone": "03-1234-5678",
        "email": "info@test.co.jp"
    }
)

# result.is_individual: False (法人)
# result.confidence: 0.95
# result.reason: "「株式会社」という法人格が含まれる"
# result.metadata: 追加情報
```

**判定基準:**

**法人の特徴:**
- 法人格: 株式会社、合同会社、有限会社、一般社団法人、NPO法人など
- 語尾: 〜会社、〜法人、〜組合、〜協会、〜財団
- 事業名: 〜商店、〜工房、〜事務所、〜スタジオ、〜ラボ
- カタカナのみの企業名

**個人の特徴:**
- 姓名の組み合わせ（例：山田太郎、佐藤花子）
- 敬称: 様、さん、殿
- 漢字2〜4文字程度で人名として自然
- フリガナや個人を示す情報

**不明な場合:**
- 屋号のみ → 個人事業主として「個人」
- 判断不可 → 安全側（法人）として判定

**ImportServiceでの統合:**

```python
from app.services.import_service import ImportService

result = ImportService.import_order_data(
    db=db,
    data=parsed_data,
    column_mapping={"顧客名": "customer_name", ...},
    use_ai_classification=True  # AI判定を有効化
)

# 新規顧客作成時にAI判定が自動実行される
# CustomerCompany.is_individual に結果が保存される
```

## Async/Sync ブリッジング

ImportServiceなど同期コンテキストでAI機能を使用する場合、`asyncio.run()`でブリッジします：

```python
import asyncio
from app.ai.factory import AIProviderFactory

# 同期関数内で
ai_provider = AIProviderFactory.create()
result = asyncio.run(
    ai_provider.classify_customer_type(
        customer_name=customer_name,
        additional_info=additional_info
    )
)
```

## エラーハンドリング

すべてのAI機能は例外をキャッチし、適切なフォールバック処理を行います：

```python
try:
    ai_provider = AIProviderFactory.create()
    result = await ai_provider.classify_customer_type(...)
    is_individual = result.is_individual

    # 信頼度チェック
    if result.confidence >= 0.7:
        warnings.append(f"AI判定: {customer_name}は{'個人' if is_individual else '法人'}")
except Exception as e:
    # フォールバック: デフォルト値を使用
    is_individual = False  # 安全側（法人）
    warnings.append(f"AI判定失敗: {str(e)}")
```

## レート制限対策

OpenAI/Anthropic APIにはレート制限があります：

**OpenAI:**
- GPT-4o: 500 requests/分, 30,000 tokens/分（Tier 1）

**対策:**
1. **リトライ機構:** OpenAI SDKは自動リトライを実装
2. **バッチ処理:** 大量データは分割して処理
3. **キャッシング:** 同じ顧客名の判定結果をキャッシュ（今後実装予定）
4. **フォールバック:** エラー時はデフォルト値を使用

**レート制限エラーの確認:**
```bash
docker-compose logs celery_worker | grep "429"
# "HTTP/1.1 429 Too Many Requests" が表示される
```

## 設定ファイル

`config/ai_settings.yaml`:

```yaml
default_provider: openai  # openai, claude, multi

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
    confidence_threshold: 0.8

  data_quality_check:
    enabled: true

  customer_classification:  # NEW
    enabled: true
    confidence_threshold: 0.7

providers:
  openai:
    model: gpt-4o
    temperature: 0.1
    max_tokens: 4000

  claude:
    model: claude-3-5-sonnet-20241022
    temperature: 0.1
    max_tokens: 4000

cost_control:
  monthly_budget: 100.0  # USD
  usage_alerts:
    enabled: true
    thresholds: [50, 80, 95]  # パーセント
```

## テスト方法

### 単体テスト

```python
import pytest
from app.ai.openai_provider import OpenAIProvider

@pytest.mark.asyncio
async def test_classify_customer_type_company():
    provider = OpenAIProvider({"model": "gpt-4o"})
    result = await provider.classify_customer_type(
        customer_name="株式会社テスト"
    )
    assert result.is_individual == False
    assert result.confidence > 0.8

@pytest.mark.asyncio
async def test_classify_customer_type_individual():
    provider = OpenAIProvider({"model": "gpt-4o"})
    result = await provider.classify_customer_type(
        customer_name="山田太郎"
    )
    assert result.is_individual == True
    assert result.confidence > 0.8
```

### 統合テスト

```bash
# テストCSVファイルを準備
cat > /tmp/test_customers.csv << EOF
顧客名,商品名,数量,単価
株式会社テスト,商品A,10,1000
山田太郎,商品B,5,2000
佐藤商店,商品C,3,1500
EOF

# APIでアップロード
curl -X POST "http://localhost:8100/api/v1/imports/upload" \
  -F "file=@/tmp/test_customers.csv" \
  -F "file_type=csv"

# ジョブ作成（AI判定有効）
curl -X POST "http://localhost:8100/api/v1/imports/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "...",
    "filename": "test_customers.csv",
    "file_type": "csv",
    "config": {"use_ai_classification": true}
  }'

# 結果確認
docker-compose exec db psql -U accusync -d accusync \
  -c "SELECT name, is_individual FROM customer_companies ORDER BY id DESC LIMIT 3;"
```

## トラブルシューティング

**問題: AI判定がすべてデフォルト値（法人）になる**
- 原因: OpenAI APIレート制限（429エラー）
- 確認: `docker-compose logs celery_worker | grep "429"`
- 対処:
  1. APIキーの確認（有効期限、クレジット残高）
  2. レート制限の解除待ち（数分〜数時間）
  3. Tier アップグレード検討
  4. Claude プロバイダーへの切り替え

**問題: "No module named 'openai'" エラー**
- 原因: OpenAI SDKがインストールされていない
- 解決: `pip install openai` または `pip install -r requirements.txt`

**問題: 判定精度が低い**
- 対処:
  1. `additional_info`に住所・電話番号・メールを追加
  2. `temperature`を下げる（0.1 → 0.05）
  3. プロンプトを改善（`openai_provider.py`のsystem_prompt）

## 今後の拡張予定

1. **判定結果キャッシュ:** 同じ顧客名の重複判定を避ける
2. **バッチ判定API:** 複数顧客を一括判定（コスト削減）
3. **学習データ蓄積:** 手動修正を学習データとして活用
4. **信頼度スコア改善:** 追加情報による精度向上
5. **多言語対応:** 英語・中国語の顧客名判定

## 参考資料

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- AI判定テスト結果: `claudedocs/ai_classification_test_results.md`
