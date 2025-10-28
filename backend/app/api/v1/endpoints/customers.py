"""Customer Company API endpoints."""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.core.database import get_db
from app.models.customer_company import CustomerCompany
from app.models.customer_identifier import CustomerIdentifier
from app.schemas.customer_company import (
    CustomerCompanyCreate,
    CustomerCompanyUpdate,
    CustomerCompanyResponse,
)


router = APIRouter()


@router.get("/", response_model=List[CustomerCompanyResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="顧客名で検索"),
    is_individual: Optional[bool] = Query(None, description="個人フラグでフィルター"),
    db: Session = Depends(get_db)
):
    """Get customers list."""
    query = db.query(CustomerCompany)

    if search:
        query = query.filter(CustomerCompany.name.ilike(f"%{search}%"))

    if is_individual is not None:
        query = query.filter(CustomerCompany.is_individual == is_individual)

    query = query.order_by(CustomerCompany.name)
    customers = query.offset(skip).limit(limit).all()

    return customers


@router.get("/{customer_id}", response_model=CustomerCompanyResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer by ID."""
    customer = db.query(CustomerCompany).filter(CustomerCompany.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )

    return customer


@router.post("/", response_model=CustomerCompanyResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: CustomerCompanyCreate,
    db: Session = Depends(get_db)
):
    """Create new customer."""
    # Generate customer code if not provided
    customer_code = customer_data.code
    if not customer_code:
        # Generate unique code: CUS + timestamp + random suffix
        import time
        import random
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        customer_code = f"CUS{timestamp}{random_suffix}"

        # Ensure uniqueness
        while db.query(CustomerCompany).filter(CustomerCompany.code == customer_code).first():
            random_suffix = random.randint(1000, 9999)
            customer_code = f"CUS{timestamp}{random_suffix}"
    else:
        # Check if code already exists
        existing = db.query(CustomerCompany).filter(CustomerCompany.code == customer_code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with code '{customer_code}' already exists"
            )

    # Create customer
    customer = CustomerCompany(
        name=customer_data.name,
        code=customer_code,
        is_individual=customer_data.is_individual,
        postal_code=customer_data.postal_code,
        address=customer_data.address,
        billing_address=customer_data.billing_address,
        phone=customer_data.phone,
        email=customer_data.email,
        contact_name=customer_data.contact_name,
        contact_email=customer_data.contact_email,
        payment_terms=customer_data.payment_terms,
        closing_day=customer_data.closing_day,
        payment_day=customer_data.payment_day,
        payment_month_offset=customer_data.payment_month_offset,
        tax_mode=customer_data.tax_mode,
        notes=customer_data.notes
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


@router.put("/{customer_id}", response_model=CustomerCompanyResponse)
def update_customer(
    customer_id: int,
    customer_data: CustomerCompanyUpdate,
    db: Session = Depends(get_db)
):
    """Update customer."""
    customer = db.query(CustomerCompany).filter(CustomerCompany.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )

    # Check if updating code to existing code
    if customer_data.code and customer_data.code != customer.code:
        existing = db.query(CustomerCompany).filter(CustomerCompany.code == customer_data.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with code '{customer_data.code}' already exists"
            )

    # Update fields
    update_data = customer_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)

    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """Delete customer."""
    customer = db.query(CustomerCompany).filter(CustomerCompany.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )

    db.delete(customer)
    db.commit()

    return None


# === 識別情報関連API ===

class CustomerIdentifierData(BaseModel):
    """顧客識別情報データ"""
    store_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    postal_code: Optional[str] = None


class DetectCustomerRequest(BaseModel):
    """顧客自動判別リクエスト"""
    identifiers: CustomerIdentifierData


class DetectCustomerResponse(BaseModel):
    """顧客自動判別レスポンス"""
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    matched_by: Optional[str] = None  # どの識別情報でマッチしたか


@router.post("/detect", response_model=DetectCustomerResponse)
def detect_customer(
    request: DetectCustomerRequest,
    db: Session = Depends(get_db)
):
    """CSVデータから顧客を自動判別

    店舗名、住所、電話番号、メールアドレスなどの識別情報を元に、
    既存の顧客を検索します。
    """
    identifiers = request.identifiers

    # 識別情報のリストを作成
    search_criteria = []
    if identifiers.store_name:
        search_criteria.append(("store_name", identifiers.store_name))
    if identifiers.phone:
        search_criteria.append(("phone", identifiers.phone))
    if identifiers.email:
        search_criteria.append(("email", identifiers.email))
    if identifiers.address:
        search_criteria.append(("address", identifiers.address))
    if identifiers.postal_code:
        search_criteria.append(("postal_code", identifiers.postal_code))

    # 各識別情報でCustomerIdentifierテーブルを検索
    for identifier_type, identifier_value in search_criteria:
        match = db.query(CustomerIdentifier).filter(
            CustomerIdentifier.identifier_type == identifier_type,
            CustomerIdentifier.identifier_value == identifier_value
        ).first()

        if match:
            customer = db.query(CustomerCompany).filter(
                CustomerCompany.id == match.customer_id
            ).first()

            if customer:
                return DetectCustomerResponse(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    matched_by=identifier_type
                )

    # マッチしなかった場合
    return DetectCustomerResponse(
        customer_id=None,
        customer_name=None,
        matched_by=None
    )


@router.post("/{customer_id}/identifiers")
def save_customer_identifiers(
    customer_id: int,
    identifiers: CustomerIdentifierData,
    db: Session = Depends(get_db)
):
    """顧客の識別情報を保存

    手動で顧客を選択した際に、CSVから抽出した識別情報を保存します。
    次回以降の自動判別に使用されます。
    """
    # 顧客の存在確認
    customer = db.query(CustomerCompany).filter(CustomerCompany.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )

    # 識別情報を保存
    saved_count = 0
    identifier_list = []

    if identifiers.store_name:
        identifier_list.append(("store_name", identifiers.store_name))
    if identifiers.phone:
        identifier_list.append(("phone", identifiers.phone))
    if identifiers.email:
        identifier_list.append(("email", identifiers.email))
    if identifiers.address:
        identifier_list.append(("address", identifiers.address))
    if identifiers.postal_code:
        identifier_list.append(("postal_code", identifiers.postal_code))

    for identifier_type, identifier_value in identifier_list:
        # 既存の識別情報をチェック（重複を避ける）
        existing = db.query(CustomerIdentifier).filter(
            CustomerIdentifier.customer_id == customer_id,
            CustomerIdentifier.identifier_type == identifier_type,
            CustomerIdentifier.identifier_value == identifier_value
        ).first()

        if not existing:
            new_identifier = CustomerIdentifier(
                customer_id=customer_id,
                identifier_type=identifier_type,
                identifier_value=identifier_value
            )
            db.add(new_identifier)
            saved_count += 1

    db.commit()

    return {
        "success": True,
        "customer_id": customer_id,
        "saved_count": saved_count,
        "message": f"{saved_count}件の識別情報を保存しました"
    }
