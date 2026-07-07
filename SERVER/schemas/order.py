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

    selling_price: Optional[float] = None


class OrderUpdate(BaseModel):
    quantity: Optional[int] = None
    status: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    final_price: Optional[float] = None




class OrderCustomerView(BaseModel):

    id: int
    product_name: str
    quantity: int
    unit_price: float 
    total_amount: float
    status: str
    customer_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class BillCustomerView(BaseModel):

    order_id: int
    shop_name: str
    items: List[dict]  
    subtotal: float
    tax: float = 0
    discount: float = 0
    grand_total: float
    customer_name: str
    customer_phone: Optional[str]
    created_at: datetime




class OrderAdminView(BaseModel):
    """Order view for shop admin - includes cost/profit breakdown"""
    id: int
    product_id: Optional[int]
    product_name: str
    quantity: int


    cost_price: Optional[float]  
    listed_price: float  
    final_price: float  
    unit_price: float
    total_amount: float


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

    order_id: int
    shop_name: str
    items: List[dict] 


    subtotal: float  
    total_cost: float  
    total_profit: float  
    total_discount_given: float  


    profit_margin_percent: float

    customer_name: str
    customer_phone: Optional[str]
    created_at: datetime




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




class DailySalesReport(BaseModel):

    date: str
    total_orders: int
    total_revenue: float
    total_cost: float
    total_profit: float
    total_discount_given: float
    avg_profit_margin: float


class ProductProfitReport(BaseModel):

    product_id: int
    product_name: str
    units_sold: int
    total_revenue: float
    total_cost: float
    total_profit: float
    avg_selling_price: float
    avg_profit_per_unit: float
