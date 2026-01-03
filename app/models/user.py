from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"  # Shop owner
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)

    # Role
    role = Column(String(20), default=UserRole.CUSTOMER.value, index=True)

    # For Admin (shop owner) - link to their shop
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    shop = relationship("Shop", back_populates="owner")

    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN.value

    @property
    def is_shop_owner(self):
        return self.role == UserRole.ADMIN.value

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER.value
