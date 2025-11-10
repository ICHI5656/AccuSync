"""
Auto Invoice API Endpoints - 自動請求書発行API
"""

from typing import Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.auto_invoice_service import AutoInvoiceService
from app.tasks.auto_invoice_tasks import auto_generate_invoices, auto_generate_invoices_for_date


router = APIRouter()


# Pydantic schemas
class AutoInvoiceCheckResponse(BaseModel):
    """自動請求書チェックレスポンス"""
    date: date
    customers_with_closing_day: int
    customers: list


class AutoInvoiceRunRequest(BaseModel):
    """自動請求書発行リクエスト"""
    target_date: Optional[date] = Field(None, description="対象日（Noneの場合は今日）")


class AutoInvoiceRunResponse(BaseModel):
    """自動請求書発行レスポンス"""
    success: bool
    message: str
    task_id: Optional[str] = None


@router.get("/check", response_model=AutoInvoiceCheckResponse)
def check_customers_to_invoice(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    請求書を発行すべき顧客をチェック

    指定日（デフォルトは今日）が締め日の顧客を取得します。
    """
    if target_date is None:
        target_date = datetime.now().date()

    customers = AutoInvoiceService.get_customers_to_invoice(db, target_date)

    return {
        'date': target_date,
        'customers_with_closing_day': len(customers),
        'customers': [
            {
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'closing_day': c.closing_day,
                'payment_day': c.payment_day,
                'payment_month_offset': c.payment_month_offset
            }
            for c in customers
        ]
    }


@router.post("/run", response_model=AutoInvoiceRunResponse)
def run_auto_invoice_generation(
    request: AutoInvoiceRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    自動請求書発行を実行

    指定日（デフォルトは今日）の自動請求書発行を実行します。
    バックグラウンドタスクとして非同期に実行されます。
    """
    target_date = request.target_date or datetime.now().date()

    # Celeryタスクをキューに追加
    if request.target_date:
        task = auto_generate_invoices_for_date.delay(target_date.strftime("%Y-%m-%d"))
    else:
        task = auto_generate_invoices.delay()

    return {
        'success': True,
        'message': f'自動請求書発行タスクをキューに追加しました（対象日: {target_date}）',
        'task_id': task.id
    }


@router.post("/run-sync")
def run_auto_invoice_generation_sync(
    request: AutoInvoiceRunRequest,
    db: Session = Depends(get_db)
):
    """
    自動請求書発行を同期実行（テスト用）

    指定日（デフォルトは今日）の自動請求書発行を同期的に実行します。
    結果を即座に返します。
    """
    target_date = request.target_date or datetime.now().date()

    try:
        result = AutoInvoiceService.run_auto_invoice_generation(db, target_date)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自動請求書発行中にエラーが発生しました: {str(e)}"
        )
