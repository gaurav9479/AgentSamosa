from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: str = UserRole.CUSTOMER.value


class UserCreate(UserBase):
    password: str
    shop_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    shop_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    shop_id: Optional[int] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithShop(UserResponse):
    shop_name: Optional[str] = None


class LoginResponse(BaseModel):
    user: UserResponse
    message: str = "Login successful"
