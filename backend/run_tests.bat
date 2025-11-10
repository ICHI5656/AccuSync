@echo off
REM AccuSync テスト実行スクリプト (Windows)

echo 🧪 AccuSync テストを実行します...
echo.

cd /d "%~dp0"

REM pytestがインストールされているか確認
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pytestがインストールされていません
    echo 📦 インストール中...
    pip install pytest pytest-cov
)

REM テストを実行
echo ▶️  単体テストを実行...
python -m pytest tests/test_pricing_auto_register.py::TestPricingAutoRegister -v

echo.
echo ▶️  統合テストを実行...
python -m pytest tests/test_pricing_auto_register.py::TestPricingAutoRegisterIntegration -v -m integration

echo.
echo ✅ テスト完了！
pause
