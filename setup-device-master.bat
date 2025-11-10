@echo off
REM AccuSync - Device Master Setup Script (Windows)
REM 機種マスターデータをローカルDBにセットアップします

echo ===================================================
echo AccuSync Device Master セットアップ開始
echo ===================================================
echo.

REM 1. Dockerサービスの確認
echo [ステップ1] Dockerサービスの確認
docker-compose ps | findstr "accusync-db" | findstr "Up" >nul
if errorlevel 1 (
    echo [エラー] データベースコンテナが起動していません
    echo docker-compose up -d を実行してください
    pause
    exit /b 1
)
echo [OK] データベースコンテナ起動中
echo.

REM 2. マイグレーションの実行
echo [ステップ2] データベースマイグレーション
echo device_attributes テーブルを作成します...
docker-compose exec -T api alembic upgrade head
if errorlevel 1 (
    echo [エラー] マイグレーション失敗
    pause
    exit /b 1
)
echo [OK] マイグレーション完了
echo.

REM 3. サンプルデータの投入
echo [ステップ3] 機種マスターデータの投入
echo 約90機種のサイズ情報を登録します...

REM SQLファイルをコンテナ内にコピー
docker cp backend\scripts\seed_device_data.sql accusync-db:/tmp/seed_device_data.sql

REM SQL実行
docker-compose exec -T db psql -U accusync -d accusync -f /tmp/seed_device_data.sql >nul 2>&1
if errorlevel 1 (
    echo [警告] サンプルデータ投入をスキップ（既に存在する可能性があります）
) else (
    echo [OK] サンプルデータ投入完了
)
echo.

REM 4. データ確認
echo [ステップ4] データ確認
for /f %%i in ('docker-compose exec -T db psql -U accusync -d accusync -t -c "SELECT COUNT(*) FROM device_attributes;"') do set COUNT=%%i
echo [OK] 登録済み機種数: %COUNT%件
echo.

REM 5. サービス再起動
echo [ステップ5] サービス再起動
echo 変更を反映します...
docker-compose restart api celery_worker
echo [OK] サービス再起動完了
echo.

REM 完了メッセージ
echo ===================================================
echo セットアップ完了！
echo ===================================================
echo.
echo [完了] device_attributes テーブル作成
echo [完了] 機種マスターデータ登録（%COUNT%件）
echo [完了] サービス再起動
echo.
echo これで別のネットワーク環境でも機種抽出とサイズ取得が動作します！
echo.
echo [確認方法]
echo docker-compose exec db psql -U accusync -d accusync
echo SELECT brand, device_name, size_category FROM device_attributes LIMIT 10;
echo.
pause
