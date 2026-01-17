
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.core.models import TimeStampedModel

class DiscountType(str, PyEnum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BOGO = "bogo"

class Coupon(TimeStampedModel):
    __tablename__ = "coupons"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType))
    value: Mapped[float] = mapped_column(Float)
    min_spend: Mapped[float] = mapped_column(Float, default=0.0)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class AutomaticDiscount(TimeStampedModel):
    __tablename__ = "automatic_discounts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    configuration: Mapped[dict] = mapped_column(JSON, default={})



class Affiliate(TimeStampedModel):
    __tablename__ = "affiliates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    unique_code: Mapped[str] = mapped_column(String, unique=True)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.10)
    total_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    user: Mapped["app.modules.auth.models.User"] = relationship("app.modules.auth.models.User")

class Campaign(TimeStampedModel):
    __tablename__ = "campaigns"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer_groups.id"))
    group: Mapped["app.modules.customers.models.CustomerGroup"] = relationship("app.modules.customers.models.CustomerGroup")
