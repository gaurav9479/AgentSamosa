from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ShopCategory(Base):
    """Categories for shops - e.g., Beauty, Grocery, Clothing, Footwear"""
    __tablename__ = "shop_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)
    icon = Column(String(50), nullable=True)  # emoji or icon name
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    shops = relationship("Shop", back_populates="category")


class Shop(Base):
    """Individual shops/stores in the marketplace"""
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    banner_url = Column(String(500), nullable=True)

    # Category
    category_id = Column(Integer, ForeignKey("shop_categories.id"), nullable=True)

    # Owner Info
    owner_name = Column(String(200), nullable=True)
    owner_email = Column(String(200), nullable=True)
    owner_phone = Column(String(20), nullable=True)

    # Location
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)

    # Business Info
    gst_number = Column(String(50), nullable=True)

    # Metrics
    rating = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("ShopCategory", back_populates="shops")
    products = relationship("Product", back_populates="shop")
    orders = relationship("Order", back_populates="shop")
    owner = relationship("User", back_populates="shop", uselist=False)
