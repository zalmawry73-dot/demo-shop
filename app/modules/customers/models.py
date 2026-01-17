from sqlalchemy import String, Integer, DateTime, Enum, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from app.core.models import TimeStampedModel
from datetime import datetime
import enum

class CustomerType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class Customer(TimeStampedModel):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    mobile: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Address
    country: Mapped[str] = mapped_column(String(100), default="Saudi Arabia")
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Details
    customer_type: Mapped[CustomerType] = mapped_column(Enum(CustomerType), default=CustomerType.INDIVIDUAL)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=True)
    dob: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Business
    channel: Mapped[str] = mapped_column(String(50), default="Store")
    points: Mapped[int] = mapped_column(Integer, default=0)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # Soft delete

    # Relationships
    orders: Mapped[List["app.modules.sales.models.Order"]] = relationship("app.modules.sales.models.Order", back_populates="customer")
    carts: Mapped[List["app.modules.sales.models.AbandonedCart"]] = relationship("app.modules.sales.models.AbandonedCart", back_populates="customer")

class CustomerGroup(TimeStampedModel):
    __tablename__ = "customer_groups"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    criteria: Mapped[dict] = mapped_column(JSON, default={})
