"""Customer Company schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CustomerCompanyBase(BaseModel):
    """Base Customer Company schema."""
    name: str = Field(..., description="会社名・個人名", min_length=1, max_length=200)
    code: Optional[str] = Field(None, description="顧客コード", max_length=50)
    is_individual: bool = Field(False, description="個人フラグ（True=個人、False=法人）")
    postal_code: Optional[str] = Field(None, description="郵便番号", max_length=20)
    address: Optional[str] = Field(None, description="住所", max_length=500)
    billing_address: Optional[str] = Field(None, description="請求先住所", max_length=500)
    phone: Optional[str] = Field(None, description="電話番号", max_length=50)
    email: Optional[str] = Field(None, description="メールアドレス", max_length=200)
    contact_name: Optional[str] = Field(None, description="担当者名", max_length=100)
    contact_email: Optional[str] = Field(None, description="担当者メール", max_length=200)
    payment_terms: Optional[str] = Field(None, description="支払条件（説明文）", max_length=200)
    closing_day: Optional[int] = Field(None, description="締め日（1-31、0=月末）", ge=0, le=31)
    payment_day: Optional[int] = Field(None, description="支払い日（1-31、0=月末）", ge=0, le=31)
    payment_month_offset: Optional[int] = Field(1, description="支払い月のオフセット（0=当月、1=翌月、2=翌々月）", ge=0, le=12)
    tax_mode: Optional[str] = Field('inclusive', description="税込/税抜（inclusive/exclusive）")
    notes: Optional[str] = Field(None, description="備考")


class CustomerCompanyCreate(CustomerCompanyBase):
    """Create Customer Company request."""
    pass


class CustomerCompanyUpdate(BaseModel):
    """Update Customer Company request."""
    name: Optional[str] = Field(None, description="会社名・個人名", min_length=1, max_length=200)
    code: Optional[str] = Field(None, description="顧客コード", max_length=50)
    is_individual: Optional[bool] = Field(None, description="個人フラグ")
    postal_code: Optional[str] = Field(None, description="郵便番号", max_length=20)
    address: Optional[str] = Field(None, description="住所", max_length=500)
    billing_address: Optional[str] = Field(None, description="請求先住所", max_length=500)
    phone: Optional[str] = Field(None, description="電話番号", max_length=50)
    email: Optional[str] = Field(None, description="メールアドレス", max_length=200)
    contact_name: Optional[str] = Field(None, description="担当者名", max_length=100)
    contact_email: Optional[str] = Field(None, description="担当者メール", max_length=200)
    payment_terms: Optional[str] = Field(None, description="支払条件（説明文）", max_length=200)
    closing_day: Optional[int] = Field(None, description="締め日（1-31、0=月末）", ge=0, le=31)
    payment_day: Optional[int] = Field(None, description="支払い日（1-31、0=月末）", ge=0, le=31)
    payment_month_offset: Optional[int] = Field(None, description="支払い月のオフセット（0=当月、1=翌月、2=翌々月）", ge=0, le=12)
    tax_mode: Optional[str] = Field(None, description="税込/税抜")
    notes: Optional[str] = Field(None, description="備考")


class CustomerCompanyResponse(CustomerCompanyBase):
    """Customer Company response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
