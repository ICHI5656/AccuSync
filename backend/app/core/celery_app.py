"""Celery Application Configuration"""

from celery import Celery

from app.core.config import settings

# Celeryアプリケーションの作成
celery_app = Celery(
    "accusync",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']  # タスクモジュール
)

# Celery設定
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tokyo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分
    task_soft_time_limit=25 * 60,  # 25分
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat スケジュール設定
celery_app.conf.beat_schedule = {
    'auto-generate-invoices-daily': {
        'task': 'auto_generate_invoices',
        'schedule': 3600.0,  # 1時間ごと（テスト用）本番では86400.0（1日）に変更
        'options': {
            'expires': 3600,  # 1時間以内に実行されなければ期限切れ
        }
    },
    'sync-device-master-daily': {
        'task': 'sync_device_master_from_supabase',
        'schedule': 86400.0,  # 毎日1回（24時間ごと）
        'options': {
            'expires': 7200,  # 2時間以内に実行されなければ期限切れ
        }
    },
}

# タスク自動検出設定
celery_app.autodiscover_tasks(['app.tasks'])
