"""Pricing Rule schemas."""

from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class PricingRuleBase(BaseModel):
    """Base Pricing Rule schema."""
    customer_id: int = Field(..., description="顧客ID")
    product_id: Optional[int] = Field(None, description="商品ID（個別商品指定の場合）")
    product_type_keyword: Optional[str] = Field(None, description="商品タイプキーワード（商品タイプ指定の場合）")
    price: Decimal = Field(..., description="適用単価")
    min_qty: Optional[int] = Field(None, description="最小数量")
    start_date: Optional[date] = Field(None, description="適用開始日")
    end_date: Optional[date] = Field(None, description="適用終了日")
    priority: int = Field(0, description="優先度")


class PricingRuleCreate(PricingRuleBase):
    """Create Pricing Rule request."""

    @field_validator('product_type_keyword')
    @classmethod
    def validate_product_reference(cls, v, info):
        """Validate that either product_id or product_type_keyword is provided."""
        product_id = info.data.get('product_id')
        if not product_id and not v:
            raise ValueError('Either product_id or product_type_keyword must be provided')
        return v


class PricingRuleUpdate(BaseModel):
    """Update Pricing Rule request."""
    price: Optional[Decimal] = Field(None, description="適用単価")
    min_qty: Optional[int] = Field(None, description="最小数量")
    start_date: Optional[date] = Field(None, description="適用開始日")
    end_date: Optional[date] = Field(None, description="適用終了日")
    priority: Optional[int] = Field(None, description="優先度")


class PricingRuleResponse(PricingRuleBase):
    """Pricing Rule response."""
    id: int
    customer_name: Optional[str] = Field(None, description="顧客名")
    product_name: Optional[str] = Field(None, description="商品名（product_id指定時）")
    product_sku: Optional[str] = Field(None, description="商品SKU（product_id指定時）")
    product_type_keyword: Optional[str] = Field(None, description="商品タイプキーワード（商品タイプ指定時）")

    class Config:
        from_attributes = True
