from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from models import InventoryItem, Warehouse, StockMovement, StockMovementReason

async def get_withdrawal_plan(session: AsyncSession, variant_id: int, requested_qty: int) -> List[Dict]:
    """
    Priority Withdrawal Algorithm:
    1. Find all warehouses with stock for this variant.
    2. Sort by Warehouse Priority (High priority first? Index 0 is usually highest priority).
       Let's assume priority_index ASC (0, 1, 2...) = First, Second, Third.
    3. Fulfill requested_qty greedily.
    """
    stmt = (
        select(InventoryItem)
        .join(Warehouse)
        .where(InventoryItem.variant_id == variant_id)
        .where(InventoryItem.quantity > 0)
        .order_by(Warehouse.priority_index.asc())
    )
    
    result = await session.execute(stmt)
    inventory_items = result.scalars().all()
    
    plan = []
    remaining_qty = requested_qty
    
    for item in inventory_items:
        if remaining_qty <= 0:
            break
            
        take_qty = min(item.quantity, remaining_qty)
        plan.append({
            "warehouse_id": item.warehouse_id,
            "warehouse_name": item.warehouse.name, # Assumes lazy load or joined load needs options if async
            "take_qty": take_qty
        })
        
        remaining_qty -= take_qty
        
    if remaining_qty > 0:
        # Not enough stock
        return [{"error": "Insufficient stock", "missing": remaining_qty}]
        
    return plan

async def create_stock_movement(
    session: AsyncSession, 
    variant_id: int, 
    warehouse_id: int, 
    qty_change: int, 
    reason: StockMovementReason,
    related_id: Optional[int] = None
):
    """
    Logs the movement and updates the InventoryItem quantity.
    """
    # 1. Log Movement
    movement = StockMovement(
        variant_id=variant_id,
        warehouse_id=warehouse_id,
        qty_change=qty_change,
        reason=reason,
        related_id=related_id
    )
    session.add(movement)
    
    # 2. Update Inventory
    # Check if item exists
    stmt = select(InventoryItem).where(InventoryItem.variant_id == variant_id, InventoryItem.warehouse_id == warehouse_id)
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    
    if item:
        item.quantity += qty_change
    else:
        # Create new if adding stock
        if qty_change > 0:
            new_item = InventoryItem(variant_id=variant_id, warehouse_id=warehouse_id, quantity=qty_change)
            session.add(new_item)
        else:
            raise ValueError("Cannot deduct stock from non-existent inventory item")
            
    await session.commit()
