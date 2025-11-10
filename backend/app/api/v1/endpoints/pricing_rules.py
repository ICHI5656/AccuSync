"""Pricing Rules API endpoints."""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.pricing_rule import PricingRule
from app.models.customer_company import CustomerCompany
from app.models.product import Product
from app.schemas.pricing_rule import (
    PricingRuleCreate,
    PricingRuleUpdate,
    PricingRuleResponse,
)


router = APIRouter()


@router.get("/", response_model=List[PricingRuleResponse])
def list_pricing_rules(
    customer_id: Optional[int] = Query(None, description="顧客IDでフィルター"),
    product_id: Optional[int] = Query(None, description="商品IDでフィルター"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get pricing rules list."""
    query = db.query(PricingRule)

    if customer_id:
        query = query.filter(PricingRule.customer_id == customer_id)
    if product_id:
        query = query.filter(PricingRule.product_id == product_id)

    rules = query.offset(skip).limit(limit).all()

    # Enrich with customer and product names
    result = []
    for rule in rules:
        customer = db.query(CustomerCompany).filter(CustomerCompany.id == rule.customer_id).first()
        product = db.query(Product).filter(Product.id == rule.product_id).first() if rule.product_id else None

        rule_dict = {
            "id": rule.id,
            "customer_id": rule.customer_id,
            "product_id": rule.product_id,
            "product_type_keyword": rule.product_type_keyword,
            "price": rule.price,
            "min_qty": rule.min_qty,
            "start_date": rule.start_date,
            "end_date": rule.end_date,
            "priority": rule.priority,
            "customer_name": customer.name if customer else None,
            "product_name": product.name if product else None,
            "product_sku": product.sku if product else None,
        }
        result.append(PricingRuleResponse(**rule_dict))

    return result


@router.get("/{rule_id}", response_model=PricingRuleResponse)
def get_pricing_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get pricing rule by ID."""
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule {rule_id} not found"
        )

    customer = db.query(CustomerCompany).filter(CustomerCompany.id == rule.customer_id).first()
    product = db.query(Product).filter(Product.id == rule.product_id).first() if rule.product_id else None

    rule_dict = {
        "id": rule.id,
        "customer_id": rule.customer_id,
        "product_id": rule.product_id,
        "product_type_keyword": rule.product_type_keyword,
        "price": rule.price,
        "min_qty": rule.min_qty,
        "start_date": rule.start_date,
        "end_date": rule.end_date,
        "priority": rule.priority,
        "customer_name": customer.name if customer else None,
        "product_name": product.name if product else None,
        "product_sku": product.sku if product else None,
    }

    return PricingRuleResponse(**rule_dict)


@router.post("/", response_model=PricingRuleResponse, status_code=status.HTTP_201_CREATED)
def create_pricing_rule(
    rule_data: PricingRuleCreate,
    db: Session = Depends(get_db)
):
    """Create new pricing rule."""
    # Verify at least one of product_id or product_type_keyword is provided
    if not rule_data.product_id and not rule_data.product_type_keyword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either product_id or product_type_keyword must be provided"
        )

    # Verify customer exists
    customer = db.query(CustomerCompany).filter(CustomerCompany.id == rule_data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {rule_data.customer_id} not found"
        )

    # Verify product exists if product_id is provided
    product = None
    if rule_data.product_id:
        product = db.query(Product).filter(Product.id == rule_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {rule_data.product_id} not found"
            )

    # Create pricing rule
    rule = PricingRule(
        customer_id=rule_data.customer_id,
        product_id=rule_data.product_id,
        product_type_keyword=rule_data.product_type_keyword,
        price=rule_data.price,
        min_qty=rule_data.min_qty,
        start_date=rule_data.start_date,
        end_date=rule_data.end_date,
        priority=rule_data.priority
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    rule_dict = {
        "id": rule.id,
        "customer_id": rule.customer_id,
        "product_id": rule.product_id,
        "product_type_keyword": rule.product_type_keyword,
        "price": rule.price,
        "min_qty": rule.min_qty,
        "start_date": rule.start_date,
        "end_date": rule.end_date,
        "priority": rule.priority,
        "customer_name": customer.name,
        "product_name": product.name if product else None,
        "product_sku": product.sku if product else None,
    }

    return PricingRuleResponse(**rule_dict)


@router.put("/{rule_id}", response_model=PricingRuleResponse)
def update_pricing_rule(
    rule_id: int,
    rule_data: PricingRuleUpdate,
    db: Session = Depends(get_db)
):
    """Update pricing rule."""
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule {rule_id} not found"
        )

    # Update fields
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)

    customer = db.query(CustomerCompany).filter(CustomerCompany.id == rule.customer_id).first()
    product = db.query(Product).filter(Product.id == rule.product_id).first() if rule.product_id else None

    rule_dict = {
        "id": rule.id,
        "customer_id": rule.customer_id,
        "product_id": rule.product_id,
        "product_type_keyword": rule.product_type_keyword,
        "price": rule.price,
        "min_qty": rule.min_qty,
        "start_date": rule.start_date,
        "end_date": rule.end_date,
        "priority": rule.priority,
        "customer_name": customer.name if customer else None,
        "product_name": product.name if product else None,
        "product_sku": product.sku if product else None,
    }

    return PricingRuleResponse(**rule_dict)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pricing_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete pricing rule."""
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule {rule_id} not found"
        )

    db.delete(rule)
    db.commit()

    return None


@router.get("/customer/{customer_id}/products", response_model=List[PricingRuleResponse])
def get_customer_pricing_rules(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get all pricing rules for a customer."""
    # Verify customer exists
    customer = db.query(CustomerCompany).filter(CustomerCompany.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )

    rules = db.query(PricingRule).filter(PricingRule.customer_id == customer_id).all()

    result = []
    for rule in rules:
        product = db.query(Product).filter(Product.id == rule.product_id).first() if rule.product_id else None

        rule_dict = {
            "id": rule.id,
            "customer_id": rule.customer_id,
            "product_id": rule.product_id,
            "product_type_keyword": rule.product_type_keyword,
            "price": rule.price,
            "min_qty": rule.min_qty,
            "start_date": rule.start_date,
            "end_date": rule.end_date,
            "priority": rule.priority,
            "customer_name": customer.name,
            "product_name": product.name if product else None,
            "product_sku": product.sku if product else None,
        }
        result.append(PricingRuleResponse(**rule_dict))

    return result
