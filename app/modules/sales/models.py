
from typing import List, Optional
from enum import Enum as PyEnum
from sqlalchemy import String, Float, Boolean, ForeignKey, Text, Enum, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models import TimeStampedModel, Base
# We reference other modules by string to avoid circular imports at module level
# Relationships will be resolved by SQLAlchemy Registry

class OrderStatus(str, PyEnum):
    NEW = "new"
    PENDING_PAYMENT = "pending_payment"
    PROCESSING = "processing"
    READY = "ready"
    SHIPPING = "shipping"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    old_status: Mapped[Optional[str]] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50))
    changed_by: Mapped[Optional[str]] = mapped_column(String(100)) # User name or "System"
    created_at: Mapped[str] = mapped_column(String(50)) # ISO format timestamp (Simulated datetime)

    order: Mapped["Order"] = relationship("Order", back_populates="history")

class AbandonedCart(TimeStampedModel):
    __tablename__ = "abandoned_carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    customer_group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer_groups.id")) 
    items: Mapped[dict] = mapped_column(JSON) 
    recovery_status: Mapped[str] = mapped_column(String(50), default="pending")

    customer: Mapped["app.modules.customers.models.Customer"] = relationship("app.modules.customers.models.Customer", back_populates="carts")
    # Lazy string reference
    customer_group: Mapped[Optional["app.modules.customers.models.CustomerGroup"]] = relationship("app.modules.customers.models.CustomerGroup")

class Order(TimeStampedModel):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.NEW)
    payment_status: Mapped[str] = mapped_column(String(50))
    payment_method: Mapped[str] = mapped_column(String(50))
    
    shipping_company: Mapped[Optional[str]] = mapped_column(String(100))
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)

    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    
    affiliate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("affiliates.id"), nullable=True)
    affiliate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("affiliates.id"), nullable=True)
    discount_detail: Mapped[dict] = mapped_column(JSON, default={})
    payment_details: Mapped[dict] = mapped_column(JSON, default={})

    customer: Mapped["app.modules.customers.models.Customer"] = relationship("app.modules.customers.models.Customer", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    shipping_address: Mapped[Optional["ShippingAddress"]] = relationship("ShippingAddress", uselist=False, back_populates="order", cascade="all, delete-orphan")
    affiliate: Mapped[Optional["app.modules.marketing.models.Affiliate"]] = relationship("app.modules.marketing.models.Affiliate")
    history: Mapped[List["OrderStatusHistory"]] = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"))
    
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    # String reference to Catalog Module
    variant: Mapped["app.modules.catalog.models.ProductVariant"] = relationship("app.modules.catalog.models.ProductVariant")

class ShippingAddress(Base):
    __tablename__ = "shipping_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    address_lines: Mapped[str] = mapped_column(Text)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    order: Mapped["Order"] = relationship("Order", back_populates="shipping_address")
