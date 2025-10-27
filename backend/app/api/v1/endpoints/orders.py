"""
Orders API endpoints.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.core.database import get_db
from app.models.order import Order, OrderItem
from app.models.customer_company import CustomerCompany
from app.models.issuer_company import IssuerCompany
from app.models.product import Product
from pydantic import BaseModel, Field


router = APIRouter()


class OrderItemResponse(BaseModel):
    """Order item response."""
    id: int
    product_id: int
    product_name: str
    product_sku: str
    qty: int
    unit_price: Decimal
    subtotal_ex_tax: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_in_tax: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response."""
    id: int
    order_no: str
    order_date: date
    customer_id: int
    customer_name: str
    customer_code: str
    is_individual: bool
    issuer_id: int | None
    issuer_name: str | None
    source: str
    memo: str | None
    items: List[OrderItemResponse]
    total_amount: Decimal

    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    """Order summary statistics."""
    total_orders: int
    total_amount: Decimal
    customer_count: int


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    db: Session = Depends(get_db),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of orders to return")
):
    """
    Get list of orders with filters.
    """
    try:
        query = db.query(Order)

        # Apply filters
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        
        if end_date:
            query = query.filter(Order.order_date <= end_date)

        # Order by date descending
        query = query.order_by(Order.order_date.desc(), Order.id.desc())

        # Apply limit
        orders = query.limit(limit).all()

        # Build response
        result = []
        for order in orders:
            # Get customer info
            customer = db.query(CustomerCompany).filter(
                CustomerCompany.id == order.customer_id
            ).first()

            # Get issuer info
            issuer = db.query(IssuerCompany).filter(
                IssuerCompany.id == order.issuer_company_id
            ).first()

            # Get order items
            items_query = db.query(OrderItem).filter(
                OrderItem.order_id == order.id
            ).all()

            items = []
            total_amount = Decimal('0')
            for item in items_query:
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).first()

                items.append(OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=product.name if product else "Unknown",
                    product_sku=product.sku if product else "",
                    qty=item.qty,
                    unit_price=item.unit_price,
                    subtotal_ex_tax=item.subtotal_ex_tax,
                    tax_rate=item.tax_rate,
                    tax_amount=item.tax_amount,
                    total_in_tax=item.total_in_tax
                ))
                total_amount += item.total_in_tax

            result.append(OrderResponse(
                id=order.id,
                order_no=order.order_no,
                order_date=order.order_date,
                customer_id=order.customer_id,
                customer_name=customer.name if customer else "Unknown",
                customer_code=customer.code if customer else "",
                is_individual=customer.is_individual if customer else False,
                issuer_id=order.issuer_company_id if order.issuer_company_id else None,
                issuer_name=issuer.name if issuer else None,
                source=order.source,
                memo=order.memo,
                items=items,
                total_amount=total_amount
            ))

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve orders: {str(e)}"
        )


@router.get("/summary", response_model=OrderSummary)
async def get_order_summary(
    db: Session = Depends(get_db),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date")
):
    """
    Get order summary statistics.
    """
    try:
        # Base query for orders
        order_query = db.query(Order)
        
        if customer_id:
            order_query = order_query.filter(Order.customer_id == customer_id)
        
        if start_date:
            order_query = order_query.filter(Order.order_date >= start_date)
        
        if end_date:
            order_query = order_query.filter(Order.order_date <= end_date)

        # Count orders
        total_orders = order_query.count()

        # Get order IDs for item sum
        order_ids = [o.id for o in order_query.all()]

        # Calculate total amount
        if order_ids:
            total_amount = db.query(
                func.sum(OrderItem.total_in_tax)
            ).filter(
                OrderItem.order_id.in_(order_ids)
            ).scalar() or Decimal('0')
        else:
            total_amount = Decimal('0')

        # Count unique customers
        customer_count = db.query(
            func.count(func.distinct(Order.customer_id))
        ).filter(
            Order.id.in_(order_ids) if order_ids else False
        ).scalar() or 0

        return OrderSummary(
            total_orders=total_orders,
            total_amount=total_amount,
            customer_count=customer_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve summary: {str(e)}"
        )
