from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from SERVER.core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)


    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)


    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(255), nullable=False)  
    quantity = Column(Integer, nullable=False)


    cost_price = Column(Float, nullable=True)  
    listed_price = Column(Float, nullable=False) 
    final_price = Column(Float, nullable=False) 
    unit_price = Column(Float, nullable=False)  
    total_amount = Column(Float, nullable=False)  


    total_cost = Column(Float, nullable=True)  
    profit = Column(Float, nullable=True)  
    discount_given = Column(Float, default=0)  


    status = Column(String(50), default=OrderStatus.PENDING.value)


    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    delivery_address = Column(String(500), nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


    shop = relationship("Shop", back_populates="orders")
