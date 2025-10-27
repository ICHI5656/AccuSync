"""
Settings API endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from app.core.database import get_db
from app.core.config import settings
from app.models.customer_company import CustomerCompany
from app.models.product import Product
from app.models.order import Order
from app.models.issuer_company import IssuerCompany
from app.services.issuer_service import IssuerService
from pydantic import BaseModel, Field


router = APIRouter()


class DatabaseStatsResponse(BaseModel):
    """Database statistics response."""
    companies: int = Field(..., description="Number of companies")
    individuals: int = Field(..., description="Number of individual customers")
    products: int = Field(..., description="Number of products")
    orders: int = Field(..., description="Number of orders")
    connection_status: str = Field(..., description="Database connection status")


class IssuerInfoUpdate(BaseModel):
    """Issuer information update request."""
    name: str = Field(..., description="Company name")
    brand_name: str | None = Field(None, description="Brand name")
    tax_id: str | None = Field(None, description="Tax ID number")
    address: str | None = Field(None, description="Address")
    tel: str | None = Field(None, description="Phone number")
    email: str | None = Field(None, description="Email address")
    bank_info: str | None = Field(None, description="Bank account information")
    invoice_notes: str | None = Field(None, description="Invoice notes")


class IssuerInfoResponse(BaseModel):
    """Issuer information response."""
    id: int
    name: str
    brand_name: str | None
    tax_id: str | None
    address: str | None
    tel: str | None
    email: str | None
    bank_info: str | None
    invoice_notes: str | None

    class Config:
        from_attributes = True


@router.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(db: Session = Depends(get_db)):
    """
    Get database statistics.
    """
    try:
        # Count companies and individuals
        companies_count = db.query(CustomerCompany).filter(
            CustomerCompany.is_individual == False
        ).count()

        individuals_count = db.query(CustomerCompany).filter(
            CustomerCompany.is_individual == True
        ).count()

        # Count products
        products_count = db.query(Product).count()

        # Count orders
        orders_count = db.query(Order).count()

        return DatabaseStatsResponse(
            companies=companies_count,
            individuals=individuals_count,
            products=products_count,
            orders=orders_count,
            connection_status="connected"
        )

    except Exception as e:
        return DatabaseStatsResponse(
            companies=0,
            individuals=0,
            products=0,
            orders=0,
            connection_status="error"
        )


@router.get("/issuer", response_model=IssuerInfoResponse)
async def get_issuer_info(db: Session = Depends(get_db)):
    """
    Get default issuer company information.
    """
    issuer = IssuerService.get_default_issuer(db)

    if not issuer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Default issuer not found"
        )

    return IssuerInfoResponse.from_orm(issuer)


@router.put("/issuer", response_model=IssuerInfoResponse)
async def update_issuer_info(
    data: IssuerInfoUpdate,
    db: Session = Depends(get_db)
):
    """
    Update default issuer company information.
    """
    try:
        # Get or create default issuer
        issuer = IssuerService.get_default_issuer(db)

        if not issuer:
            # Create new issuer
            issuer = IssuerCompany(
                name=data.name,
                brand_name=data.brand_name,
                tax_id=data.tax_id,
                address=data.address,
                tel=data.tel,
                email=data.email,
                bank_info=data.bank_info,
                invoice_notes=data.invoice_notes or 'お支払いは請求書記載の期日までにお願いいたします。'
            )
            db.add(issuer)
        else:
            # Update existing issuer
            issuer.name = data.name
            issuer.brand_name = data.brand_name
            issuer.tax_id = data.tax_id
            issuer.address = data.address
            issuer.tel = data.tel
            issuer.email = data.email
            issuer.bank_info = data.bank_info
            if data.invoice_notes:
                issuer.invoice_notes = data.invoice_notes

        db.commit()
        db.refresh(issuer)

        return IssuerInfoResponse.from_orm(issuer)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update issuer information: {str(e)}"
        )


@router.get("/issuer/list", response_model=List[IssuerInfoResponse])
async def list_issuers(db: Session = Depends(get_db)):
    """
    Get list of all issuer companies.
    """
    try:
        issuers = db.query(IssuerCompany).all()
        return [IssuerInfoResponse.from_orm(issuer) for issuer in issuers]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve issuer list: {str(e)}"
        )


class AISettingsResponse(BaseModel):
    """AI settings response."""
    ai_provider: str = Field(..., description="AI provider (openai or claude)")
    has_api_key: bool = Field(..., description="Whether API key is configured")
    auto_mapping_enabled: bool = Field(True, description="Auto-mapping feature enabled")
    quality_check_enabled: bool = Field(True, description="Quality check feature enabled")
    confidence_threshold: float = Field(0.8, description="Confidence threshold (0.0-1.0)")


class CustomerCompanyResponse(BaseModel):
    """Customer company response."""
    id: int
    code: str
    name: str
    is_individual: bool
    address: str | None
    postal_code: str | None
    phone: str | None
    email: str | None

    class Config:
        from_attributes = True


@router.get("/ai", response_model=AISettingsResponse)
async def get_ai_settings():
    """
    Get AI settings from environment variables.
    """
    # Check if API keys are configured
    has_api_key = False
    if settings.AI_PROVIDER == "openai":
        has_api_key = bool(settings.OPENAI_API_KEY)
    elif settings.AI_PROVIDER == "claude":
        has_api_key = bool(settings.ANTHROPIC_API_KEY)

    return AISettingsResponse(
        ai_provider=settings.AI_PROVIDER,
        has_api_key=has_api_key,
        auto_mapping_enabled=True,  # デフォルト値
        quality_check_enabled=True,  # デフォルト値
        confidence_threshold=0.8  # デフォルト値
    )


@router.get("/customers", response_model=List[CustomerCompanyResponse])
async def list_customers(
    db: Session = Depends(get_db),
    is_individual: bool | None = None
):
    """
    Get list of customer companies.

    Args:
        is_individual: Filter by individual (True) or company (False). If None, return all.
    """
    try:
        query = db.query(CustomerCompany)

        if is_individual is not None:
            query = query.filter(CustomerCompany.is_individual == is_individual)

        customers = query.order_by(CustomerCompany.name).all()
        return [CustomerCompanyResponse.from_orm(customer) for customer in customers]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve customer list: {str(e)}"
        )
