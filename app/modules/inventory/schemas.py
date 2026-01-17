from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from app.modules.inventory.models import BranchType, StockMovementReason

class WarehouseBase(BaseModel):
    name: str
    name_en: Optional[str] = None
    country: Optional[str] = "السعودية"
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    branch_type: BranchType = BranchType.WAREHOUSE
    priority_index: int = 0
    is_active: bool = True

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(WarehouseBase):
    pass

class WarehouseResponse(WarehouseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class InventoryUpdateItem(BaseModel):
    variant_id: str
    warehouse_id: int
    new_quantity: int

class BatchInventoryUpdate(BaseModel):
    reason: StockMovementReason = StockMovementReason.MANUAL_EDIT
    updates: List[InventoryUpdateItem]

class StockTakingBase(BaseModel):
    warehouse_id: int
    name: str
    type: str = "partial" # partial, full
    notes: Optional[str] = None

class StockTakingCreate(StockTakingBase):
    pass

class StockTakingItemUpdate(BaseModel):
    variant_id: str
    counted_qty: int

class StockTakingResponse(StockTakingBase):
    id: int
    status: str
    completed_at: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TransferItem(BaseModel):
    variant_id: str
    qty: int

class TransferRequestBase(BaseModel):
    source_wh_id: int
    destination_wh_id: int
    items: List[TransferItem] = []

class TransferRequestCreate(TransferRequestBase):
    pass

class TransferRequestUpdate(BaseModel):
    source_wh_id: Optional[int] = None
    destination_wh_id: Optional[int] = None
    items: Optional[List[TransferItem]] = None
    status: Optional[str] = None # draft, approved, shipped, received

class TransferRequestResponse(TransferRequestBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    # We might want to include relation details like warehouse names or product names
    # but for now let's keep it simple or use a separate "Detail" schema
    model_config = ConfigDict(from_attributes=True)
