"""
Products API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from decimal import Decimal
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.product import Product
from app.models.pricing_rule import PricingRule
from app.models.customer_company import CustomerCompany


router = APIRouter()


class ProductCreate(BaseModel):
    """商品作成リクエスト"""
    sku: str = Field(..., min_length=1, max_length=100, description="商品コード（SKU）")
    name: str = Field(..., min_length=1, max_length=500, description="商品名")
    default_price: Decimal = Field(..., gt=0, description="標準単価")
    tax_rate: Decimal = Field(0.10, ge=0, le=1, description="税率")
    tax_category: str = Field("standard", description="税区分")
    unit: str = Field("個", max_length=20, description="単位")
    is_active: bool = Field(True, description="有効フラグ")


class ProductUpdate(BaseModel):
    """商品更新リクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    default_price: Optional[Decimal] = Field(None, gt=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    tax_category: Optional[str] = None
    unit: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """商品レスポンス"""
    id: int
    sku: str
    name: str
    default_price: Decimal
    tax_rate: Decimal
    tax_category: str
    unit: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PricingRuleCreate(BaseModel):
    """価格ルール作成リクエスト"""
    customer_id: int = Field(..., description="取引先ID")
    product_id: int = Field(..., description="商品ID")
    price: Decimal = Field(..., gt=0, description="適用単価")
    min_qty: Optional[int] = Field(None, gt=0, description="最小数量")
    start_date: Optional[str] = Field(None, description="適用開始日（YYYY-MM-DD）")
    end_date: Optional[str] = Field(None, description="適用終了日（YYYY-MM-DD）")
    priority: int = Field(0, description="優先度")


class PricingRuleResponse(BaseModel):
    """価格ルールレスポンス"""
    id: int
    customer_id: int
    customer_name: str
    product_id: int
    product_sku: str
    product_name: str
    price: Decimal
    min_qty: int | None
    start_date: str | None
    end_date: str | None
    priority: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="商品名またはSKUで検索"),
    is_active: Optional[bool] = Query(None, description="有効/無効フィルター"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    商品一覧を取得
    """
    try:
        query = db.query(Product)

        if search:
            query = query.filter(
                or_(
                    Product.name.contains(search),
                    Product.sku.contains(search)
                )
            )

        if is_active is not None:
            query = query.filter(Product.is_active == is_active)

        products = query.order_by(Product.created_at.desc()).limit(limit).all()

        return [
            ProductResponse(
                id=p.id,
                sku=p.sku,
                name=p.name,
                default_price=p.default_price,
                tax_rate=p.tax_rate,
                tax_category=p.tax_category,
                unit=p.unit,
                is_active=p.is_active,
                created_at=p.created_at.isoformat() if p.created_at else "",
                updated_at=p.updated_at.isoformat() if p.updated_at else ""
            )
            for p in products
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve products: {str(e)}"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    特定の商品を取得
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )

        return ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            default_price=product.default_price,
            tax_rate=product.tax_rate,
            tax_category=product.tax_category,
            unit=product.unit,
            is_active=product.is_active,
            created_at=product.created_at.isoformat() if product.created_at else "",
            updated_at=product.updated_at.isoformat() if product.updated_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve product: {str(e)}"
        )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    新しい商品を作成
    """
    try:
        # SKUの重複チェック
        existing = db.query(Product).filter(Product.sku == request.sku).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{request.sku}' already exists"
            )

        product = Product(
            sku=request.sku,
            name=request.name,
            default_price=request.default_price,
            tax_rate=request.tax_rate,
            tax_category=request.tax_category,
            unit=request.unit,
            is_active=request.is_active
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            default_price=product.default_price,
            tax_rate=product.tax_rate,
            tax_category=product.tax_category,
            unit=product.unit,
            is_active=product.is_active,
            created_at=product.created_at.isoformat() if product.created_at else "",
            updated_at=product.updated_at.isoformat() if product.updated_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    request: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    商品を更新
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )

        # 更新
        if request.name is not None:
            product.name = request.name
        if request.default_price is not None:
            product.default_price = request.default_price
        if request.tax_rate is not None:
            product.tax_rate = request.tax_rate
        if request.tax_category is not None:
            product.tax_category = request.tax_category
        if request.unit is not None:
            product.unit = request.unit
        if request.is_active is not None:
            product.is_active = request.is_active

        db.commit()
        db.refresh(product)

        return ProductResponse(
            id=product.id,
            sku=product.sku,
            name=product.name,
            default_price=product.default_price,
            tax_rate=product.tax_rate,
            tax_category=product.tax_category,
            unit=product.unit,
            is_active=product.is_active,
            created_at=product.created_at.isoformat() if product.created_at else "",
            updated_at=product.updated_at.isoformat() if product.updated_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}"
        )


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    商品を削除（論理削除）
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )

        # 論理削除
        product.is_active = False
        db.commit()

        return {"success": True, "message": f"Product {product_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}"
        )


@router.get("/{product_id}/pricing", response_model=List[PricingRuleResponse])
async def get_product_pricing_rules(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    特定商品の価格ルール一覧を取得
    """
    try:
        rules = db.query(PricingRule).filter(
            PricingRule.product_id == product_id
        ).all()

        result = []
        for rule in rules:
            customer = db.query(CustomerCompany).filter(
                CustomerCompany.id == rule.customer_id
            ).first()

            product = db.query(Product).filter(
                Product.id == rule.product_id
            ).first()

            result.append(PricingRuleResponse(
                id=rule.id,
                customer_id=rule.customer_id,
                customer_name=customer.name if customer else "Unknown",
                product_id=rule.product_id,
                product_sku=product.sku if product else "",
                product_name=product.name if product else "Unknown",
                price=rule.price,
                min_qty=rule.min_qty,
                start_date=rule.start_date.isoformat() if rule.start_date else None,
                end_date=rule.end_date.isoformat() if rule.end_date else None,
                priority=rule.priority
            ))

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pricing rules: {str(e)}"
        )


@router.post("/pricing", response_model=PricingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule(
    request: PricingRuleCreate,
    db: Session = Depends(get_db)
):
    """
    新しい価格ルールを作成
    """
    try:
        # 顧客と商品の存在確認
        customer = db.query(CustomerCompany).filter(
            CustomerCompany.id == request.customer_id
        ).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {request.customer_id} not found"
            )

        product = db.query(Product).filter(
            Product.id == request.product_id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {request.product_id} not found"
            )

        rule = PricingRule(
            customer_id=request.customer_id,
            product_id=request.product_id,
            price=request.price,
            min_qty=request.min_qty,
            start_date=request.start_date,
            end_date=request.end_date,
            priority=request.priority
        )

        db.add(rule)
        db.commit()
        db.refresh(rule)

        return PricingRuleResponse(
            id=rule.id,
            customer_id=rule.customer_id,
            customer_name=customer.name,
            product_id=rule.product_id,
            product_sku=product.sku,
            product_name=product.name,
            price=rule.price,
            min_qty=rule.min_qty,
            start_date=rule.start_date.isoformat() if rule.start_date else None,
            end_date=rule.end_date.isoformat() if rule.end_date else None,
            priority=rule.priority
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pricing rule: {str(e)}"
        )


@router.delete("/pricing/{rule_id}")
async def delete_pricing_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    価格ルールを削除
    """
    try:
        rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pricing rule {rule_id} not found"
            )

        db.delete(rule)
        db.commit()

        return {"success": True, "message": f"Pricing rule {rule_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pricing rule: {str(e)}"
        )
