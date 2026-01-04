from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

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
    cost_price = Column(Float, nullable=True)  # Purchase cost (admin only)
    price = Column(Float, nullable=False)  # MRP / Display price
    min_price = Column(Float, nullable=True)  # Minimum acceptable price for bargaining
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

    # Expiry & Clearance (for perishable items like groceries, cosmetics)
    is_perishable = Column(Boolean, default=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    expiry_alert_days = Column(Integer, default=30)  # Days before expiry to trigger alert
    clearance_discount = Column(Float, default=20.0)  # Discount percentage when on clearance
    is_on_clearance = Column(Boolean, default=False)  # Auto-set when expiring soon

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

    @property
    def days_until_expiry(self):
        """Calculate days until expiry date"""
        if not self.expiry_date:
            return None
        now = datetime.now(timezone.utc)
        expiry = self.expiry_date if self.expiry_date.tzinfo else self.expiry_date.replace(tzinfo=timezone.utc)
        delta = expiry - now
        return delta.days

    @property
    def is_expiring_soon(self):
        """Check if product is expiring within alert days"""
        if not self.is_perishable or not self.expiry_date:
            return False
        days = self.days_until_expiry
        return days is not None and 0 < days <= self.expiry_alert_days

    @property
    def is_expired(self):
        """Check if product has expired"""
        if not self.expiry_date:
            return False
        days = self.days_until_expiry
        return days is not None and days <= 0

    @property
    def clearance_price(self):
        """Calculate clearance price with discount"""
        if not self.is_on_clearance or not self.clearance_discount:
            return None
        return round(self.price * (1 - self.clearance_discount / 100), 2)

    @property
    def expiry_status(self):
        """Get expiry status string"""
        if not self.is_perishable or not self.expiry_date:
            return "not_perishable"
        if self.is_expired:
            return "expired"
        elif self.is_expiring_soon:
            return "expiring_soon"
        return "fresh"
