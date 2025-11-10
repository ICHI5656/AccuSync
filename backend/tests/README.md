# AccuSync テストガイド

## テストの実行方法

### 方法1: スクリプトを使用（簡単）

**Linux/Mac:**
```bash
cd backend
chmod +x run_tests.sh
./run_tests.sh
```

**Windows:**
```bash
cd backend
run_tests.bat
```

### 方法2: pytestコマンドを直接実行

**全テスト実行:**
```bash
cd backend
pytest tests/ -v
```

**特定のテストのみ実行:**
```bash
# 単体テストのみ
pytest tests/test_pricing_auto_register.py::TestPricingAutoRegister -v

# 統合テストのみ
pytest tests/test_pricing_auto_register.py::TestPricingAutoRegisterIntegration -v
```

**カバレッジレポート付き:**
```bash
pytest tests/ --cov=app --cov-report=html
```

## テストの種類

### 単体テスト (Unit Tests)
- 個別の関数やメソッドが正しく動作するか確認
- データベース不要、高速実行
- 例: `test_extract_product_keywords_hard_case()`

### 統合テスト (Integration Tests)
- 複数のコンポーネントが連携して動作するか確認
- データベース必要、少し時間がかかる
- 例: `test_import_with_auto_pricing_registration()`

## テスト対象機能

### test_pricing_auto_register.py

**価格ルール自動登録機能**のテスト:

1. **test_auto_register_new_rule**
   - 新規価格ルールが正しく作成されるか確認

2. **test_auto_register_update_existing_rule**
   - 既存の価格ルールが正しく更新されるか確認

3. **test_auto_register_skip_same_price**
   - 同じ単価の場合はスキップされるか確認

4. **test_extract_product_keywords_***
   - 商品名からキーワードが正しく抽出されるか確認

5. **test_get_customer_price_***
   - 顧客別価格が正しく取得されるか確認

6. **test_import_with_auto_pricing_registration (統合)**
   - CSV取り込み時に価格ルールが正しく自動登録されるか確認

## テストが失敗した場合

### 1. エラーメッセージを確認

```
FAILED tests/test_pricing_auto_register.py::test_auto_register_new_rule
```

失敗したテスト名とエラー内容が表示されます。

### 2. 詳細情報を表示

```bash
pytest tests/test_pricing_auto_register.py::test_auto_register_new_rule -vv
```

`-vv` オプションでさらに詳細な情報を表示

### 3. デバッグモードで実行

```bash
pytest tests/test_pricing_auto_register.py::test_auto_register_new_rule -vv --pdb
```

`--pdb` オプションで失敗時にデバッガーが起動

## テストのメンテナンス

### 新しいテストを追加する場合

1. `tests/` ディレクトリに `test_*.py` ファイルを作成
2. テスト関数は `test_` で始める
3. 必要に応じて `conftest.py` にフィクスチャを追加

### テストデータを変更する場合

`conftest.py` の以下のフィクスチャを編集:
- `test_customer` - テスト用顧客
- `test_product_hard_case` - テスト用商品
- `sample_csv_data` - テスト用CSVデータ

## よくある質問

**Q: テストが遅いのですが？**
A: 統合テストは少し時間がかかります。単体テストのみ実行すれば高速です。

**Q: データベースエラーが出ます**
A: テスト用データベース（SQLite）は自動作成されます。エラーが出る場合は `conftest.py` を確認してください。

**Q: 環境変数は必要ですか？**
A: テストではモックデータを使用するため、環境変数は不要です。

## 参考リンク

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
