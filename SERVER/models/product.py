from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from SERVER.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)


    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    sku = Column(String(50), nullable=True, unique=True, index=True)  
    barcode = Column(String(50), nullable=True, index=True)


    cost_price = Column(Float, nullable=True)  
    price = Column(Float, nullable=False)  
    min_price = Column(Float, nullable=True)  
    compare_at_price = Column(Float, nullable=True)  


    quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=5)  
    max_stock_level = Column(Integer, nullable=True)


    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)


    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tags = Column(String(500), nullable=True)  


    sold_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)


    unit = Column(String(20), default="piece")  
    weight = Column(Float, nullable=True)  


    image_url = Column(String(500), nullable=True)
    images = Column(Text, nullable=True)  


    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)


    is_perishable = Column(Boolean, default=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    expiry_alert_days = Column(Integer, default=30)  
    clearance_discount = Column(Float, default=20.0)  
    is_on_clearance = Column(Boolean, default=False)  


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


    shop = relationship("Shop", back_populates="products")
    category = relationship("Category", back_populates="products")

    @property
    def profit_margin(self):

        if self.cost_price and self.cost_price > 0:
            return round(((self.price - self.cost_price) / self.cost_price) * 100, 2)
        return None

    @property
    def is_low_stock(self):

        return self.quantity <= self.min_stock_level

    @property
    def stock_status(self):

        if self.quantity == 0:
            return "out_of_stock"
        elif self.quantity <= self.min_stock_level:
            return "low_stock"
        return "in_stock"

    @property
    def days_until_expiry(self):

        if not self.expiry_date:
            return None
        now = datetime.now(timezone.utc)
        expiry = self.expiry_date if self.expiry_date.tzinfo else self.expiry_date.replace(tzinfo=timezone.utc)
        delta = expiry - now
        return delta.days

    @property
    def is_expiring_soon(self):

        if not self.is_perishable or not self.expiry_date:
            return False
        days = self.days_until_expiry
        return days is not None and 0 < days <= self.expiry_alert_days

    @property
    def is_expired(self):

        if not self.expiry_date:
            return False
        days = self.days_until_expiry
        return days is not None and days <= 0

    @property
    def clearance_price(self):

        if not self.is_on_clearance or not self.clearance_discount:
            return None
        return round(self.price * (1 - self.clearance_discount / 100), 2)

    @property
    def expiry_status(self):

        if not self.is_perishable or not self.expiry_date:
            return "not_perishable"
        if self.is_expired:
            return "expired"
        elif self.is_expiring_soon:
            return "expiring_soon"
        return "fresh"
