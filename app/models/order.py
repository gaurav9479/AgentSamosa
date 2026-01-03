from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    # Shop this order belongs to
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)

    # Product info
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(255), nullable=False)  # Snapshot of product name at order time
    unit_price = Column(Float, nullable=False)  # Snapshot of price at order time
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)

    # Order status
    status = Column(String(50), default=OrderStatus.PENDING.value)

    # Customer info
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    delivery_address = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shop = relationship("Shop", back_populates="orders")
