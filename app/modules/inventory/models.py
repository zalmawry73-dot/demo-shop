
from typing import List, Optional
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text, Enum, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models import TimeStampedModel

from app.modules.catalog.models import Product, ProductVariant, Category, ProductImage

class BranchType(str, PyEnum):
    WAREHOUSE = "warehouse"
    POS_POINT = "pos_point"
    BOTH = "both"

class StockMovementReason(str, PyEnum):
    NEW_ORDER = "new_order"
    CANCELLED_ORDER = "cancelled_order"
    ORDER_CANCELLED = "order_cancelled"  # Alias for consistency
    MANUAL_EDIT = "manual_edit"
    STOCK_TAKE = "stock_take"
    TRANSFER = "transfer"

class TransferStatus(str, PyEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    SHIPPED = "shipped"
    RECEIVED = "received"

class Warehouse(TimeStampedModel):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    name_en: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Detailed Address
    country: Mapped[Optional[str]] = mapped_column(String(50), default="السعودية")
    city: Mapped[Optional[str]] = mapped_column(String(50))
    district: Mapped[Optional[str]] = mapped_column(String(50))
    street: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    location: Mapped[str] = mapped_column(String(255), nullable=True) # Full address simplified
    branch_type: Mapped[BranchType] = mapped_column(Enum(BranchType), default=BranchType.WAREHOUSE)
    priority_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    inventory_items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="warehouse")

class InventoryItem(TimeStampedModel):
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint('variant_id', 'warehouse_id', name='uq_variant_warehouse'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_variants.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)

    variant: Mapped["ProductVariant"] = relationship("ProductVariant", backref="inventory_items") 
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="inventory_items")

class StockMovement(TimeStampedModel):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_variants.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    qty_change: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[StockMovementReason] = mapped_column(Enum(StockMovementReason))
    related_id: Mapped[Optional[int]] = mapped_column(Integer)
    
    variant: Mapped["ProductVariant"] = relationship("ProductVariant")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse")

class TransferRequest(TimeStampedModel):
    __tablename__ = "transfer_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_wh_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    destination_wh_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    status: Mapped[TransferStatus] = mapped_column(Enum(TransferStatus), default=TransferStatus.DRAFT)
    items: Mapped[List[dict]] = mapped_column(JSON, default=list) 

    source_warehouse: Mapped["Warehouse"] = relationship("Warehouse", foreign_keys=[source_wh_id])
    destination_warehouse: Mapped["Warehouse"] = relationship("Warehouse", foreign_keys=[destination_wh_id])

class StockTakingStatus(str, PyEnum):
    DRAFT = "draft"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class StockTaking(TimeStampedModel):
    __tablename__ = "stock_takings"

    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50), default="partial") # partial, full
    status: Mapped[StockTakingStatus] = mapped_column(Enum(StockTakingStatus), default=StockTakingStatus.DRAFT)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[str]] = mapped_column(String(50)) # Isoformat date

    warehouse: Mapped["Warehouse"] = relationship("Warehouse")
    items: Mapped[List["StockTakingItem"]] = relationship("StockTakingItem", back_populates="stock_taking", cascade="all, delete-orphan")

class StockTakingItem(TimeStampedModel):
    __tablename__ = "stock_taking_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    stock_taking_id: Mapped[int] = mapped_column(ForeignKey("stock_takings.id"))
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_variants.id"))
    
    expected_qty: Mapped[int] = mapped_column(Integer, default=0)
    counted_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Null means not counted yet
    
    stock_taking: Mapped["StockTaking"] = relationship("StockTaking", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant")
