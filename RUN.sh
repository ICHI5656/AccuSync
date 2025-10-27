#!/bin/bash

echo "🚀 AccuSync 起動スクリプト"
echo "======================================"
echo ""

# カレントディレクトリ確認
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ エラー: docker-compose.yml が見つかりません"
    echo "   このスクリプトはプロジェクトルートで実行してください"
    exit 1
fi

# Docker確認
if ! command -v docker-compose &> /dev/null; then
    echo "❌ エラー: docker-compose がインストールされていません"
    exit 1
fi

echo "✅ Docker環境を確認しました"
echo ""

# 既存コンテナの確認
if [ "$(docker-compose ps -q)" ]; then
    echo "⚠️  既存のコンテナが起動しています"
    read -p "停止して再起動しますか？ (y/N): " answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        echo "🛑 コンテナを停止中..."
        docker-compose down
    else
        echo "ℹ️  既存のコンテナを維持します"
    fi
fi

echo ""
echo "🔨 Dockerコンテナをビルド＆起動中..."
echo "   初回は数分かかります。お待ちください..."
docker-compose up -d --build

echo ""
echo "⏳ サービスの起動を待機中..."
sleep 5

# ヘルスチェック
echo ""
echo "🏥 ヘルスチェック実行中..."

max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8100/health > /dev/null 2>&1; then
        echo "✅ Backend API: 起動完了"
        break
    fi
    attempt=$((attempt + 1))
    echo "   待機中... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Backend APIの起動に失敗しました"
    echo "   ログを確認してください: docker-compose logs -f api"
    exit 1
fi

# データベースマイグレーション確認
echo ""
read -p "データベースマイグレーションを実行しますか？ (初回のみ必要) (y/N): " migrate
if [ "$migrate" = "y" ] || [ "$migrate" = "Y" ]; then
    echo "📊 マイグレーション実行中..."
    docker-compose exec -T api alembic revision --autogenerate -m "Initial migration" 2>/dev/null
    docker-compose exec -T api alembic upgrade head
    echo "✅ マイグレーション完了"
fi

echo ""
echo "======================================"
echo "🎉 AccuSync が起動しました！"
echo "======================================"
echo ""
echo "📍 アクセスURL:"
echo "   Frontend:     http://localhost:3100"
echo "   API Docs:     http://localhost:8100/docs"
echo "   Health Check: http://localhost:8100/health"
echo "   MinIO Console: http://localhost:9101"
echo ""
echo "🛠️  便利なコマンド:"
echo "   ログ確認:     docker-compose logs -f"
echo "   停止:         docker-compose down"
echo "   再起動:       docker-compose restart"
echo ""
echo "📚 詳細は START_HERE.md と DOCKER_GUIDE.md をご覧ください"
echo ""

