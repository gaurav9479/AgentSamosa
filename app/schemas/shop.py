from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== SHOP CATEGORY SCHEMAS ==============

class ShopCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0


class ShopCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ShopCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    image_url: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ShopCategoryWithCount(ShopCategoryResponse):
    shop_count: int = 0


# ============== SHOP SCHEMAS ==============

class ShopCreate(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    category_id: Optional[int] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None


class ShopUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    category_id: Optional[int] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    owner_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class ShopResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    logo_url: Optional[str]
    banner_url: Optional[str]
    category_id: Optional[int]
    owner_name: Optional[str]
    owner_email: Optional[str]
    owner_phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    pincode: Optional[str]
    rating: float
    total_orders: int
    total_revenue: float
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ShopWithCategory(ShopResponse):
    category: Optional[ShopCategoryResponse] = None
    product_count: int = 0


class ShopDashboardStats(BaseModel):
    """Dashboard stats for shop owner"""
    total_products: int = 0
    active_products: int = 0
    low_stock_count: int = 0
    out_of_stock_count: int = 0
    total_orders: int = 0
    pending_orders: int = 0
    today_orders: int = 0
    total_revenue: float = 0.0
    today_revenue: float = 0.0
    total_customers: int = 0
    inventory_value: float = 0.0
