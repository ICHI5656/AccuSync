#!/bin/bash
# AccuSync テスト実行スクリプト

echo "🧪 AccuSync テストを実行します..."
echo ""

cd "$(dirname "$0")"

# 仮想環境がある場合はアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# pytestがインストールされているか確認
if ! command -v pytest &> /dev/null; then
    echo "❌ pytestがインストールされていません"
    echo "📦 インストール中..."
    pip install pytest pytest-cov
fi

# テストを実行
echo "▶️  単体テストを実行..."
pytest tests/test_pricing_auto_register.py::TestPricingAutoRegister -v

echo ""
echo "▶️  統合テストを実行..."
pytest tests/test_pricing_auto_register.py::TestPricingAutoRegisterIntegration -v -m integration

echo ""
echo "✅ テスト完了！"
