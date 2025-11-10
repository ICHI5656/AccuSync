#!/bin/bash
# AccuSync - Device Master Setup Script
# 機種マスターデータをローカルDBにセットアップします

set -e

echo "🚀 AccuSync Device Master セットアップ開始"
echo "================================================"

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Dockerサービスが起動しているか確認
echo ""
echo "📋 ステップ1: Dockerサービスの確認"
if ! docker-compose ps | grep -q "accusync-db.*Up"; then
    echo -e "${YELLOW}⚠️  データベースコンテナが起動していません${NC}"
    echo "   docker-compose up -d を実行してください"
    exit 1
fi
echo -e "${GREEN}✅ データベースコンテナ起動中${NC}"

# 2. マイグレーションの実行
echo ""
echo "📋 ステップ2: データベースマイグレーション"
echo "   device_attributes テーブルを作成します..."

docker-compose exec -T api alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ マイグレーション完了${NC}"
else
    echo -e "${RED}❌ マイグレーション失敗${NC}"
    exit 1
fi

# 3. サンプルデータの投入
echo ""
echo "📋 ステップ3: 機種マスターデータの投入"
echo "   約90機種のサイズ情報を登録します..."

# SQLファイルをコンテナ内にコピー
docker cp backend/scripts/seed_device_data.sql accusync-db:/tmp/seed_device_data.sql

# SQL実行
docker-compose exec -T db psql -U accusync -d accusync -f /tmp/seed_device_data.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ サンプルデータ投入完了${NC}"
else
    echo -e "${YELLOW}⚠️  サンプルデータ投入をスキップ（既に存在する可能性があります）${NC}"
fi

# 4. データ確認
echo ""
echo "📋 ステップ4: データ確認"
COUNT=$(docker-compose exec -T db psql -U accusync -d accusync -t -c "SELECT COUNT(*) FROM device_attributes;" | tr -d ' ')

if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ 登録済み機種数: ${COUNT}件${NC}"
else
    echo -e "${RED}❌ データが登録されていません${NC}"
    exit 1
fi

# 5. サービス再起動
echo ""
echo "📋 ステップ5: サービス再起動"
echo "   変更を反映します..."

docker-compose restart api celery_worker

echo -e "${GREEN}✅ サービス再起動完了${NC}"

# 完了メッセージ
echo ""
echo "================================================"
echo -e "${GREEN}🎉 セットアップ完了！${NC}"
echo ""
echo "✅ device_attributes テーブル作成"
echo "✅ 機種マスターデータ登録（${COUNT}件）"
echo "✅ サービス再起動"
echo ""
echo "💡 これで別のネットワーク環境でも機種抽出とサイズ取得が動作します！"
echo ""
echo "📊 確認方法:"
echo "   docker-compose exec db psql -U accusync -d accusync"
echo "   SELECT brand, device_name, size_category FROM device_attributes LIMIT 10;"
echo ""
