from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    customer_name: str
    customer_email: Optional[str] = None


class OrderUpdate(BaseModel):
    quantity: Optional[int] = None
    status: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_amount: float
    status: str
    customer_name: str
    customer_email: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
