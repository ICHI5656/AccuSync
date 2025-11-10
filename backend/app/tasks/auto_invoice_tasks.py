"""
Auto Invoice Tasks - 自動請求書発行タスク

Celery Beat による定期実行タスク
"""

from datetime import datetime
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.auto_invoice_service import AutoInvoiceService

logger = logging.getLogger(__name__)


@celery_app.task(name="auto_generate_invoices")
def auto_generate_invoices():
    """自動請求書生成タスク

    毎日実行され、締め日の顧客に対して請求書を自動生成します。
    """
    logger.info("Starting auto invoice generation task")

    db = SessionLocal()
    try:
        # 今日の日付で自動生成を実行
        result = AutoInvoiceService.run_auto_invoice_generation(db)

        logger.info(
            f"Auto invoice generation completed: "
            f"{result['invoices_generated']} generated, "
            f"{result['invoices_skipped']} skipped, "
            f"{result['errors']} errors"
        )

        return result

    except Exception as e:
        logger.error(f"Error in auto invoice generation task: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name="auto_generate_invoices_for_date")
def auto_generate_invoices_for_date(date_str: str):
    """指定日の自動請求書生成タスク

    Args:
        date_str: 日付文字列（YYYY-MM-DD形式）
    """
    logger.info(f"Starting auto invoice generation for date: {date_str}")

    db = SessionLocal()
    try:
        # 日付文字列をdateオブジェクトに変換
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # 指定日で自動生成を実行
        result = AutoInvoiceService.run_auto_invoice_generation(db, target_date)

        logger.info(
            f"Auto invoice generation for {date_str} completed: "
            f"{result['invoices_generated']} generated, "
            f"{result['invoices_skipped']} skipped, "
            f"{result['errors']} errors"
        )

        return result

    except Exception as e:
        logger.error(f"Error in auto invoice generation for {date_str}: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'date': date_str
        }
    finally:
        db.close()
