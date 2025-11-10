"""
Invoice API Endpoints - 請求書API
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.invoice import Invoice, InvoiceItem
from app.services.invoice_service import InvoiceService
# from app.services.pdf_service import PDFService  # 一時無効化（Dockerイメージ再ビルド必要）


router = APIRouter()


# Pydantic schemas
class InvoiceItemResponse(BaseModel):
    """請求書明細レスポンス"""
    id: int
    product_id: Optional[int]
    description: str
    qty: int
    unit_price: float
    tax_rate: float
    subtotal_ex_tax: float
    tax_amount: float
    total_in_tax: float

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """請求書レスポンス"""
    id: int
    invoice_no: str
    issuer_company_id: int
    customer_id: int
    period_start: date
    period_end: date
    issue_date: date
    due_date: date
    subtotal_ex_tax: float
    tax_amount: float
    total_in_tax: float
    status: str
    notes: Optional[str]
    pdf_url: Optional[str]
    items: List[InvoiceItemResponse] = []
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class InvoiceCreateRequest(BaseModel):
    """請求書作成リクエスト"""
    customer_id: int = Field(..., description="取引先ID")
    period_start: date = Field(..., description="集計期間開始日")
    period_end: date = Field(..., description="集計期間終了日")
    issuer_id: Optional[int] = Field(None, description="発行会社ID（任意）")
    notes: Optional[str] = Field(None, description="備考")


class InvoiceAggregatePreviewRequest(BaseModel):
    """請求書集計プレビューリクエスト"""
    customer_id: int = Field(..., description="取引先ID")
    period_start: date = Field(..., description="集計期間開始日")
    period_end: date = Field(..., description="集計期間終了日")
    issuer_id: Optional[int] = Field(None, description="発行会社ID（任意）")


@router.post("/preview", status_code=status.HTTP_200_OK)
def preview_invoice_aggregation(
    request: InvoiceAggregatePreviewRequest,
    db: Session = Depends(get_db)
):
    """
    請求書集計プレビュー

    指定期間の注文を集計して、請求書を作成せずにプレビュー表示
    """
    try:
        aggregation = InvoiceService.aggregate_orders_for_invoice(
            db=db,
            customer_id=request.customer_id,
            period_start=request.period_start,
            period_end=request.period_end,
            issuer_id=request.issuer_id
        )

        if not aggregation['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=aggregation['error']
            )

        return aggregation

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"請求書集計プレビュー中にエラーが発生しました: {str(e)}"
        )


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    request: InvoiceCreateRequest,
    db: Session = Depends(get_db)
):
    """
    請求書を作成

    指定期間の注文を集計して請求書を作成します。
    """
    try:
        invoice = InvoiceService.create_invoice(
            db=db,
            customer_id=request.customer_id,
            period_start=request.period_start,
            period_end=request.period_end,
            issuer_id=request.issuer_id,
            notes=request.notes
        )

        return invoice

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"請求書作成中にエラーが発生しました: {str(e)}"
        )


@router.get("/", response_model=List[InvoiceResponse])
def list_invoices(
    customer_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    請求書一覧を取得

    Args:
        customer_id: 取引先IDでフィルター（任意）
        status_filter: ステータスでフィルター（任意）: draft, issued, paid, void
        skip: スキップ件数
        limit: 取得件数上限
    """
    query = db.query(Invoice)

    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    # 発行日の降順でソート
    query = query.order_by(Invoice.issue_date.desc())

    invoices = query.offset(skip).limit(limit).all()

    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    請求書詳細を取得
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"請求書ID {invoice_id} が見つかりません"
        )

    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    notes: Optional[str] = None,
    status_update: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    請求書を更新

    Args:
        invoice_id: 請求書ID
        notes: 備考（任意）
        status_update: ステータス更新（任意）: draft, issued, paid, void
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"請求書ID {invoice_id} が見つかりません"
        )

    # 更新
    if notes is not None:
        invoice.notes = notes

    if status_update is not None:
        valid_statuses = ['draft', 'issued', 'paid', 'void']
        if status_update not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無効なステータス: {status_update}。有効な値: {', '.join(valid_statuses)}"
            )
        invoice.status = status_update

    db.commit()
    db.refresh(invoice)

    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    請求書を削除

    ステータスが'issued', 'paid'の請求書は削除できません。
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"請求書ID {invoice_id} が見つかりません"
        )

    # 発行済み・支払済みの請求書は削除不可
    if invoice.status in ['issued', 'paid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ステータスが'{invoice.status}'の請求書は削除できません"
        )

    db.delete(invoice)
    db.commit()


# PDF生成エンドポイント（一時無効化 - Dockerイメージ再ビルド必要）
# @router.get("/{invoice_id}/pdf")
# def generate_invoice_pdf(
#     invoice_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     請求書PDFを生成
#
#     指定された請求書IDからPDFファイルを生成してダウンロードします。
#     """
#     try:
#         # 請求書データを取得
#         invoice_data = InvoiceService.get_invoice_preview_data(db, invoice_id)
#
#         # PDFを生成
#         pdf_service = PDFService()
#         pdf_bytes = pdf_service.generate_invoice_pdf(invoice_data)
#
#         # PDFをレスポンスとして返す
#         from fastapi.responses import Response
#         return Response(
#             content=pdf_bytes,
#             media_type="application/pdf",
#             headers={
#                 "Content-Disposition": f"attachment; filename=invoice_{invoice_data['invoice_no']}.pdf"
#             }
#         )
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=str(e)
#         )
#     except ImportError as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"PDF生成ライブラリが利用できません: {str(e)}。Dockerコンテナで実行してください。"
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"PDF生成中にエラーが発生しました: {str(e)}"
#         )
