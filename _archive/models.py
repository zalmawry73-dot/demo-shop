from datetime import datetime
from typing import List, Optional, Dict
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Text, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Base Model
class Base(DeclarativeBase):
    pass

class TimeStampedModel(Base):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Enums
class ProductType(str, PyEnum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    FOOD = "food"

class OrderStatus(str, PyEnum):
    NEW = "new"
    PENDING_PAYMENT = "pending_payment"
    PROCESSING = "processing"
    READY = "ready"
    SHIPPING = "shipping"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class UserRole(str, PyEnum):
    ADMIN = "admin"
    MERCHANT = "merchant"
    STAFF = "staff"

class StockMovementReason(str, PyEnum):
    NEW_ORDER = "new_order"
    CANCELLED_ORDER = "cancelled_order"
    MANUAL_EDIT = "manual_edit"
    STOCK_TAKE = "stock_take"
    TRANSFER = "transfer"

class BranchType(str, PyEnum):
    WAREHOUSE = "warehouse"
    POS_POINT = "pos_point"
    BOTH = "both"

class ShippingConditionType(str, PyEnum):
    FIXED = "fixed"
    WEIGHT_BASED = "weight_based"
    PRICE_BASED = "price_based"

class TransferStatus(str, PyEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    SHIPPED = "shipped"
    RECEIVED = "received"

# 1. Product Catalog
class Category(TimeStampedModel):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))

    # Hierarchy
    parent: Mapped[Optional["Category"]] = relationship("Category", remote_side=[id], back_populates="sub_categories")
    sub_categories: Mapped[List["Category"]] = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")

class Product(TimeStampedModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    product_type: Mapped[ProductType] = mapped_column(Enum(ProductType), default=ProductType.PHYSICAL)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    weight: Mapped[Optional[float]] = mapped_column(Float, comment="Weight in kg")
    
    # SEO
    seo_title: Mapped[Optional[str]] = mapped_column(String(255))
    seo_description: Mapped[Optional[str]] = mapped_column(Text)

    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

class ProductVariant(TimeStampedModel):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    cost_price: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Attributes for Color/Size etc. e.g., {"color": "Red", "size": "XL"}
    # This allows unlimited variant options without schema changes
    attributes: Mapped[dict] = mapped_column(JSON, default={})

    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    inventory_items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="variant")

class ProductImage(TimeStampedModel):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    image_url: Mapped[str] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    product: Mapped["Product"] = relationship("Product", back_populates="images")

# 2. Multi-Warehouse Inventory
class Warehouse(TimeStampedModel):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(255))
    branch_type: Mapped[BranchType] = mapped_column(Enum(BranchType), default=BranchType.WAREHOUSE)
    priority_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    inventory_items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="warehouse")

class InventoryItem(TimeStampedModel):
    """
    Solves the Multi-Warehouse Requirement:
    Instead of storing 'quantity' on the Product or Variant directly, we decouple it.
    This table acts as a pivot between specific Product Variants and Warehouses.
    It allows tracking that Variant A has 10 units in Warehouse X and 5 units in Warehouse Y.
    Total stock for a variant is the sum of quantities across all warehouses.
    """
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint('variant_id', 'warehouse_id', name='uq_variant_warehouse'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)

    variant: Mapped["ProductVariant"] = relationship("ProductVariant", back_populates="inventory_items")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="inventory_items")

class StockMovement(TimeStampedModel):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    qty_change: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[StockMovementReason] = mapped_column(Enum(StockMovementReason))
    related_id: Mapped[Optional[int]] = mapped_column(Integer, comment="ID of Order or Transfer depending on reason")
    
    variant: Mapped["ProductVariant"] = relationship("ProductVariant")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")

class TransferRequest(TimeStampedModel):
    __tablename__ = "transfer_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_wh_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    destination_wh_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    status: Mapped[TransferStatus] = mapped_column(Enum(TransferStatus), default=TransferStatus.DRAFT)
    # Simple JSON structure for items: {"variant_id": quantity, ...}
    items: Mapped[dict] = mapped_column(JSON) 

    source_warehouse: Mapped["Warehouse"] = relationship("Warehouse", foreign_keys=[source_wh_id])
    destination_warehouse: Mapped["Warehouse"] = relationship("Warehouse", foreign_keys=[destination_wh_id])

# 4. Customers & Marketing
class Customer(TimeStampedModel):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    note: Mapped[Optional[str]] = mapped_column(Text)
    tag: Mapped[Optional[str]] = mapped_column(String(50))

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")
    carts: Mapped[List["AbandonedCart"]] = relationship("AbandonedCart", back_populates="customer")

class AbandonedCart(TimeStampedModel):
    __tablename__ = "abandoned_carts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    customer_group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer_groups.id")) # Used for campaigns like "30% off for VIPs"
    # Items stored as JSON for flexibility in a draft state
    items: Mapped[dict] = mapped_column(JSON) 
    recovery_status: Mapped[str] = mapped_column(String(50), default="pending")

    customer: Mapped["Customer"] = relationship("Customer", back_populates="carts")
    customer_group: Mapped[Optional["CustomerGroup"]] = relationship("CustomerGroup")


# 4. Settings Module

class StoreSettings(TimeStampedModel):
    __tablename__ = "store_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    store_name: Mapped[str] = mapped_column(String(255), default="My Store")
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    support_email: Mapped[Optional[str]] = mapped_column(String(255))
    support_phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    iban: Mapped[Optional[str]] = mapped_column(String(100))
    vat_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=True, comment="Are product prices tax inclusive?")
    tax_rate: Mapped[float] = mapped_column(Float, default=0.15)


class PaymentConfig(TimeStampedModel):
    __tablename__ = "payment_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(100), unique=True) # e.g. 'stripe', 'cod'
    display_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    config: Mapped[Dict] = mapped_column(JSON, default={}) # API Keys etc


class ShippingRule(TimeStampedModel):
    __tablename__ = "shipping_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    zone: Mapped[str] = mapped_column(String(100), default="All") # e.g. 'Riyadh', 'SA'
    
    condition_type: Mapped[ShippingConditionType] = mapped_column(Enum(ShippingConditionType), default=ShippingConditionType.FIXED)
    condition_value: Mapped[float] = mapped_column(Float, default=0.0) # e.g. Weight > 5kg, Price > 500
    
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# --- Marketing & CRM ---

class DiscountType(str, PyEnum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BOGO = "bogo" # Buy X Get Y

class Coupon(TimeStampedModel):
    __tablename__ = "coupons"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    discount_type: Mapped[DiscountType] = mapped_column(Enum(DiscountType))
    value: Mapped[float] = mapped_column(Float) # e.g. 10.0 for 10% or 10 SAR
    min_spend: Mapped[float] = mapped_column(Float, default=0.0)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Max uses total
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
    
    # Configuration JSON: { "buy_product_id": 1, "get_product_id": 2, "get_quantity": 1, "discount_percent": 100 }
    configuration: Mapped[dict] = mapped_column(JSON, default={}) 

class CustomerGroup(TimeStampedModel):
    __tablename__ = "customer_groups"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    
    # Criteria JSON: { "min_orders": 5, "min_spent": 1000, "last_order_days": 30 }
    criteria: Mapped[dict] = mapped_column(JSON, default={})

class Affiliate(TimeStampedModel):
    __tablename__ = "affiliates"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    unique_code: Mapped[str] = mapped_column(String, unique=True) # URL param ?aff=code
    commission_rate: Mapped[float] = mapped_column(Float, default=0.10) # 10%
    total_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User")

class Campaign(TimeStampedModel):
    __tablename__ = "campaigns"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT") # DRAFT, SCHEDULED, SENT
    
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customer_groups.id"))
    group: Mapped["CustomerGroup"] = relationship("CustomerGroup")

class Analytics(TimeStampedModel):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True)
    visits: Mapped[int] = mapped_column(Integer, default=0)

# 3. Order Management
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

    # Supports DraftOrder requirement
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Marketing
    affiliate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("affiliates.id"), nullable=True)
    discount_detail: Mapped[dict] = mapped_column(JSON, default={}) # Stores Applied Coupons/Rules

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    shipping_address: Mapped[Optional["ShippingAddress"]] = relationship("ShippingAddress", uselist=False, back_populates="order", cascade="all, delete-orphan")
    affiliate: Mapped[Optional["Affiliate"]] = relationship("Affiliate")

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.id"))
    
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float) # Price at time of purchase

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant")

class ShippingAddress(Base):
    __tablename__ = "shipping_addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    address_lines: Mapped[str] = mapped_column(Text)
    # Map coordinates
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    order: Mapped["Order"] = relationship("Order", back_populates="shipping_address")

# 5. System
class User(TimeStampedModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STAFF)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

