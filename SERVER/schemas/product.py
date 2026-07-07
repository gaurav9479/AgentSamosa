from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime




class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    image_url: Optional[str]
    is_active: bool
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryWithProducts(CategoryResponse):
    product_count: int = 0




class ProductCreate(BaseModel):

    name: str
    price: float = Field(gt=0)


    shop_id: Optional[int] = None


    description: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None


    cost_price: Optional[float] = Field(default=None, ge=0)  
    min_price: Optional[float] = Field(default=None, ge=0)  
    compare_at_price: Optional[float] = Field(default=None, ge=0)


    quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=5, ge=0)
    max_stock_level: Optional[int] = Field(default=None, ge=0)


    category_id: Optional[int] = None
    tags: Optional[str] = None


    unit: str = "piece"
    weight: Optional[float] = None


    image_url: Optional[str] = None
    images: Optional[str] = None 


    is_featured: bool = False


    is_perishable: bool = False
    expiry_date: Optional[datetime] = None
    expiry_alert_days: int = 30
    clearance_discount: float = 20.0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    shop_id: Optional[int] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None

    cost_price: Optional[float] = None
    min_price: Optional[float] = None
    price: Optional[float] = None
    compare_at_price: Optional[float] = None

    quantity: Optional[int] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None

    category_id: Optional[int] = None
    tags: Optional[str] = None

    unit: Optional[str] = None
    weight: Optional[float] = None

    image_url: Optional[str] = None
    images: Optional[str] = None

    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


    is_perishable: Optional[bool] = None
    expiry_date: Optional[datetime] = None
    expiry_alert_days: Optional[int] = None
    clearance_discount: Optional[float] = None
    is_on_clearance: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    shop_id: Optional[int]
    description: Optional[str]
    brand: Optional[str]
    sku: Optional[str]
    barcode: Optional[str]

    cost_price: Optional[float]
    min_price: Optional[float]
    price: float
    compare_at_price: Optional[float]

    quantity: int
    min_stock_level: int
    max_stock_level: Optional[int]

    category_id: Optional[int]
    tags: Optional[str]

    sold_count: int
    view_count: int

    unit: str
    weight: Optional[float]

    image_url: Optional[str]
    images: Optional[str]

    is_active: bool
    is_featured: bool


    is_perishable: bool = False
    expiry_date: Optional[datetime] = None
    expiry_alert_days: int = 30
    clearance_discount: float = 20.0
    is_on_clearance: bool = False

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductWithCategory(ProductResponse):
    category: Optional[CategoryResponse] = None
    profit_margin: Optional[float] = None
    stock_status: str = "in_stock"


class ProductListResponse(BaseModel):

    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int




class InventoryUpdate(BaseModel):

    product_id: int
    quantity: int
    adjustment_type: str = "set"  


class LowStockAlert(BaseModel):
    product_id: int
    name: str
    current_quantity: int
    min_stock_level: int
    category: Optional[str] = None


class ExpiryAlert(BaseModel):

    product_id: int
    name: str
    shop_id: int
    shop_name: str
    expiry_date: datetime
    days_until_expiry: int
    original_price: float
    clearance_price: float
    alert_type: str   




class ProductPublicView(BaseModel):

    id: int
    name: str
    description: Optional[str]
    brand: Optional[str]
    price: float 
    compare_at_price: Optional[float]
    quantity: int
    unit: str
    image_url: Optional[str]
    is_active: bool
    stock_status: str = "in_stock"


    is_on_clearance: bool = False
    clearance_price: Optional[float] = None  

    class Config:
        from_attributes = True


class ProductAdminView(ProductResponse):

    min_price: Optional[float]
    profit_margin: Optional[float] = None
    potential_profit: Optional[float] = None  
    stock_status: str = "in_stock"


    days_until_expiry: Optional[int] = None
    expiry_status: str = "not_perishable"  
    clearance_price: Optional[float] = None

    class Config:
        from_attributes = True
