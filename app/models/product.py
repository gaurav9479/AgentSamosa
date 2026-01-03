from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


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

    # Self-referential relationship for subcategories
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True, index=True)
    sku = Column(String(50), nullable=True, unique=True, index=True)  # Stock Keeping Unit
    barcode = Column(String(50), nullable=True, index=True)

    # Pricing
    cost_price = Column(Float, nullable=True)  # Purchase cost
    price = Column(Float, nullable=False)  # Selling price
    compare_at_price = Column(Float, nullable=True)  # Original price for showing discounts

    # Inventory
    quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=5)  # Alert when stock falls below
    max_stock_level = Column(Integer, nullable=True)

    # Shop (which shop this product belongs to)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)

    # Categorization (within the shop)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags

    # Sales tracking
    sold_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Product details
    unit = Column(String(20), default="piece")  # piece, kg, liter, etc.
    weight = Column(Float, nullable=True)  # in grams

    # Media
    image_url = Column(String(500), nullable=True)
    images = Column(Text, nullable=True)  # JSON array of image URLs

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shop = relationship("Shop", back_populates="products")
    category = relationship("Category", back_populates="products")

    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price and self.cost_price > 0:
            return round(((self.price - self.cost_price) / self.cost_price) * 100, 2)
        return None

    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.quantity <= self.min_stock_level

    @property
    def stock_status(self):
        """Get stock status string"""
        if self.quantity == 0:
            return "out_of_stock"
        elif self.quantity <= self.min_stock_level:
            return "low_stock"
        return "in_stock"
