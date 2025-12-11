from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import date

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    household_size: int = 1


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    household_size: int


class ProductBase(BaseModel):
    name: str
    quantity: float
    expiration_date: date


class ProductCreate(ProductBase):
    category_id: Optional[int] = None
    notes: Optional[str] = None


class ProductOut(ProductBase):
    id: UUID
    user_id: UUID
    category_id: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ProductHistoryOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    action: str
    amount: int
    created_at: date

    class Config:
        from_attributes = True


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
