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


class ShopOwnerRegister(BaseModel):
    """Registration for shop owners - creates user + shop"""
    # User details
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    # Shop details
    shop_name: str
    shop_description: Optional[str] = None
    shop_category_id: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None  # Only for demo - in production, send via email


class VerifyResetTokenRequest(BaseModel):
    token: str


class VerifyResetTokenResponse(BaseModel):
    valid: bool
    email: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str
