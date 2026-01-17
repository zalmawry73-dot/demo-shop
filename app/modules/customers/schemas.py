from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from .models import CustomerType, Gender
import re

class CustomerBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None  # EmailStr validates format automatically
    mobile: Optional[str] = None
    country: Optional[str] = "Saudi Arabia"
    city: Optional[str] = None
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    gender: Optional[Gender] = None
    dob: Optional[datetime] = None
    channel: Optional[str] = "Store"

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    city: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    gender: Optional[Gender] = None
    dob: Optional[datetime] = None

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    points: int
    total_orders: int
    is_active: bool

    class Config:
        from_attributes = True

# --- Groups ---
class CustomerGroupBase(BaseModel):
    name: str = Field(..., max_length=100)
    criteria: dict = Field(default_factory=dict)

class CustomerGroupCreate(CustomerGroupBase):
    pass

class CustomerGroupResponse(CustomerGroupBase):
    id: int
    created_at: datetime
    customer_count: Optional[int] = 0

    class Config:
        from_attributes = True
