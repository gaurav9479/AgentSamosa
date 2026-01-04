from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    # For bargaining - if not provided, uses MRP
    selling_price: Optional[float] = None


class OrderUpdate(BaseModel):
    quantity: Optional[int] = None
    status: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    # Allow updating the final price (bargaining)
    final_price: Optional[float] = None


# ============== CUSTOMER VIEW (Public Bill) ==============

class OrderCustomerView(BaseModel):
    """Order/Bill view for customers - no cost/profit info"""
    id: int
    product_name: str
    quantity: int
    unit_price: float  # Final price per unit
    total_amount: float
    status: str
    customer_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class BillCustomerView(BaseModel):
    """Customer bill - clean view without profit info"""
    order_id: int
    shop_name: str
    items: List[dict]  # [{name, qty, unit_price, total}]
    subtotal: float
    tax: float = 0
    discount: float = 0
    grand_total: float
    customer_name: str
    customer_phone: Optional[str]
    created_at: datetime


# ============== ADMIN VIEW (With Profit Info) ==============

class OrderAdminView(BaseModel):
    """Order view for shop admin - includes cost/profit breakdown"""
    id: int
    product_id: Optional[int]
    product_name: str
    quantity: int

    # Pricing breakdown
    cost_price: Optional[float]  # What admin paid per unit
    listed_price: float  # MRP
    final_price: float  # Sold at (after bargaining)
    unit_price: float
    total_amount: float

    # Profit tracking
    total_cost: Optional[float]
    profit: Optional[float]
    discount_given: float
    profit_margin_percent: Optional[float] = None

    status: str
    customer_name: str
    customer_email: Optional[str]
    customer_phone: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BillAdminView(BaseModel):
    """Admin bill - full view with profit breakdown"""
    order_id: int
    shop_name: str
    items: List[dict]  # [{name, qty, cost, mrp, sold_at, profit}]

    # Totals
    subtotal: float  # Total amount customer pays
    total_cost: float  # What admin paid
    total_profit: float  # Revenue - Cost
    total_discount_given: float  # MRP - Sold price

    # Margins
    profit_margin_percent: float

    customer_name: str
    customer_phone: Optional[str]
    created_at: datetime


# ============== LEGACY RESPONSE (for backward compatibility) ==============

class OrderResponse(BaseModel):
    id: int
    shop_id: Optional[int]
    product_id: Optional[int]
    product_name: str
    unit_price: float
    quantity: int
    total_amount: float
    status: str
    customer_name: str
    customer_email: Optional[str]
    customer_phone: Optional[str]
    delivery_address: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============== PROFIT REPORTS ==============

class DailySalesReport(BaseModel):
    """Daily sales summary for shop admin"""
    date: str
    total_orders: int
    total_revenue: float
    total_cost: float
    total_profit: float
    total_discount_given: float
    avg_profit_margin: float


class ProductProfitReport(BaseModel):
    """Profit report per product"""
    product_id: int
    product_name: str
    units_sold: int
    total_revenue: float
    total_cost: float
    total_profit: float
    avg_selling_price: float
    avg_profit_per_unit: float
