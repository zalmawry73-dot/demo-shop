

from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from datetime import datetime
from app.modules.inventory.models import InventoryItem, Warehouse, StockMovement, StockMovementReason


async def get_withdrawal_plan(session: AsyncSession, variant_id: str, requested_qty: int) -> List[Dict]:
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
    variant_id: str, 
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

async def get_stock_movements(
    session: AsyncSession, 
    limit: int = 50, 
    offset: int = 0
) -> List[StockMovement]:
    """
    Fetch stock movements with related Variant, Product, and Warehouse.
    """
    stmt = (
        select(StockMovement)
        .join(StockMovement.variant)
        .join(StockMovement.warehouse)
        .order_by(StockMovement.created_at.desc())
        .limit(limit)
        .offset(offset)
        # Using selectinload (async friendly) if relationships are lazy
        # But here we used joins, so we can access them if eager loaded or we might need explicit options
        # For simplicity in this stack, let's assume lazy loading might fit or update query to eager load
    )
    # Eager loading optimization
    stmt = stmt.options(
        joinedload(StockMovement.warehouse),
        joinedload(StockMovement.variant).joinedload(ProductVariant.product)
    )
    
    result = await session.execute(stmt)
    return result.scalars().all()

# ----------------------------------------------------------------------
# Helper Functions for Stock Management
# ----------------------------------------------------------------------

async def get_variant_total_stock(session: AsyncSession, variant_id: str) -> int:
    """
    Get the total stock quantity for a variant across all warehouses.
    This is the single source of truth for inventory quantities.
    
    Args:
        session: Database session
        variant_id: The variant ID to check
    
    Returns:
        Total quantity across all warehouses
    """
    stmt = select(func.sum(InventoryItem.quantity)).where(InventoryItem.variant_id == variant_id)
    result = await session.execute(stmt)
    total = result.scalar_one_or_none()
    return total or 0

async def get_variant_stock_by_warehouse(
    session: AsyncSession, 
    variant_id: str
) -> List[Dict]:
    """
    Get the stock distribution for a variant across warehouses.
    
    Args:
        session: Database session
        variant_id: The variant ID to check
    
    Returns:
        List of dicts with warehouse info and quantities
        Example: [
            {"warehouse_id": 1, "warehouse_name": "Main", "quantity": 100},
            {"warehouse_id": 2, "warehouse_name": "Store 1", "quantity": 50}
        ]
    """
    stmt = (
        select(InventoryItem, Warehouse)
        .join(Warehouse)
        .where(InventoryItem.variant_id == variant_id)
        .order_by(Warehouse.priority_index)
    )
    
    result = await session.execute(stmt)
    items = result.all()
    
    return [
        {
            "warehouse_id": item.warehouse_id,
            "warehouse_name": wh.name,
            "warehouse_name_en": wh.name_en,
            "quantity": item.quantity,
            "branch_type": wh.branch_type.value
        }
        for item, wh in items
    ]

async def get_default_warehouse(session: AsyncSession) -> Optional[Warehouse]:
    """
    Get the default warehouse (usually the one with highest priority).
    Used when creating new products without specifying warehouse.
    
    Returns:
        The default warehouse (priority_index = 0) or first active warehouse
    """
    stmt = (
        select(Warehouse)
        .where(Warehouse.is_active == True)
        .order_by(Warehouse.priority_index.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def sync_variant_to_inventory(
    session: AsyncSession,
    variant_id: str,
    quantity: int,
    warehouse_id: Optional[int] = None
) -> None:
    """
    Sync a variant's initial quantity to inventory.
    Used during migration or when adding existing products.
    
    Args:
        session: Database session
        variant_id: The variant to sync
        quantity: Initial quantity to add
        warehouse_id: Target warehouse (or default if None)
    """
    if quantity <= 0:
        return
    
    # Get default warehouse if not specified
    if not warehouse_id:
        default_wh = await get_default_warehouse(session)
        if not default_wh:
            raise ValueError("No active warehouse found")
        warehouse_id = default_wh.id
    
    # Check if inventory item already exists
    stmt = select(InventoryItem).where(
        InventoryItem.variant_id == variant_id,
        InventoryItem.warehouse_id == warehouse_id
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.quantity += quantity
    else:
        # Create new
        new_item = InventoryItem(
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            quantity=quantity
        )
        session.add(new_item)
    
    # Log the movement
    movement = StockMovement(
        variant_id=variant_id,
        warehouse_id=warehouse_id,
        qty_change=quantity,
        reason=StockMovementReason.MANUAL_EDIT
    )
    session.add(movement)

# ----------------------------------------------------------------------
# Warehouse Service
# ----------------------------------------------------------------------

from app.modules.inventory.schemas import WarehouseCreate, WarehouseUpdate, BatchInventoryUpdate, StockTakingCreate

async def get_warehouses(session: AsyncSession) -> List[Warehouse]:
    stmt = select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.priority_index)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_warehouse(session: AsyncSession, warehouse_id: int) -> Optional[Warehouse]:
    stmt = select(Warehouse).where(Warehouse.id == warehouse_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_warehouse(session: AsyncSession, data: WarehouseCreate) -> Warehouse:
    warehouse = Warehouse(**data.model_dump())
    session.add(warehouse)
    await session.commit()
    await session.refresh(warehouse)
    return warehouse

async def update_warehouse(session: AsyncSession, warehouse_id: int, data: WarehouseUpdate) -> Optional[Warehouse]:
    warehouse = await get_warehouse(session, warehouse_id)
    if not warehouse:
        return None
        
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(warehouse, key, value)
        
    session.add(warehouse)
    await session.commit()
    await session.refresh(warehouse)
    return warehouse

# ----------------------------------------------------------------------
# Batch Inventory Operations
# ----------------------------------------------------------------------

async def batch_update_inventory(session: AsyncSession, batch_data: BatchInventoryUpdate):
    """
    Process multiple stock updates in a single transaction.
    Calculates the qty_change needed to reach the new_quantity.
    """
    updates = batch_data.updates
    reason = batch_data.reason
    
    for update in updates:
        # 1. Get current stock for this variant/warehouse
        stmt = select(InventoryItem).where(
            InventoryItem.variant_id == update.variant_id, 
            InventoryItem.warehouse_id == update.warehouse_id
        )
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        
        current_qty = item.quantity if item else 0
        qty_change = update.new_quantity - current_qty
        
        if qty_change == 0:
            continue
            
        # 2. Use existing create_stock_movement logic which handles logging and updating
        # Note: Avoid double commit by managing transaction at controller level ideally, 
        # but create_stock_movement commits. For batch, we might want to flush instead.
        # But to reuse code without refactoring create_stock_movement heavily, we call it.
        # It's slightly inefficient (N commits) but safe for now.
        await create_stock_movement(
            session, 
            variant_id=update.variant_id, 
            warehouse_id=update.warehouse_id, 
            qty_change=qty_change, 
            reason=reason
        )

# ----------------------------------------------------------------------
# Stock Taking Service
# ----------------------------------------------------------------------


from app.modules.inventory.models import StockTaking, StockTakingItem, StockTakingStatus, ProductVariant

async def create_stock_taking(session: AsyncSession, data: StockTakingCreate) -> StockTaking:
    # 1. Create Header
    st = StockTaking(**data.model_dump())
    st.status = StockTakingStatus.DRAFT
    session.add(st)
    await session.commit()
    await session.refresh(st)
    
    # 2. If FULL, populate all items from warehouse
    if st.type == "full":
        # Get all variants that exist in this warehouse (or all variants in system?)
        # Usually FULL means everything in the system.
        # Let's populate from existing InventoryItems + Maybe missing ones with 0?
        # For simplicity: Populate from existing Inventory Items for this warehouse.
        stmt = select(InventoryItem).where(InventoryItem.warehouse_id == st.warehouse_id)
        res = await session.execute(stmt)
        inv_items = res.scalars().all()
        
        for inv in inv_items:
            session.add(StockTakingItem(
                stock_taking_id=st.id,
                variant_id=inv.variant_id,
                expected_qty=inv.quantity,
                counted_qty=None # To be counted
            ))
        await session.commit()
        
    return st

async def get_stock_taking(session: AsyncSession, st_id: int):
    from app.modules.catalog.models import Product, ProductImage
    
    stmt = (
        select(StockTaking)
        .where(StockTaking.id == st_id)
        .options(
            selectinload(StockTaking.items)
            .joinedload(StockTakingItem.variant)
            .joinedload(ProductVariant.product)
            .selectinload(Product.images),
            joinedload(StockTaking.warehouse)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_stock_taking_item(session: AsyncSession, st_id: int, variant_id: str, counted_qty: int):
    # Find item or create if partial
    stmt = select(StockTakingItem).where(StockTakingItem.stock_taking_id == st_id, StockTakingItem.variant_id == variant_id)
    res = await session.execute(stmt)
    item = res.scalar_one_or_none()
    
    if item:
        item.counted_qty = counted_qty
    else:
        # If item not in list (e.g. found unexpected item in partial count)
        # We need its current snapshot qty?
        # Fetch current inventory
        st: StockTaking = await session.get(StockTaking, st_id)
        inv_stmt = select(InventoryItem).where(InventoryItem.variant_id == variant_id, InventoryItem.warehouse_id == st.warehouse_id)
        inv_res = await session.execute(inv_stmt)
        inv = inv_res.scalar_one_or_none()
        expected = inv.quantity if inv else 0
        
        item = StockTakingItem(
            stock_taking_id=st_id,
            variant_id=variant_id,
            expected_qty=expected,
            counted_qty=counted_qty
        )
        session.add(item)
    
    await session.commit()

async def finalize_stock_taking(session: AsyncSession, st_id: int):
    st = await get_stock_taking(session, st_id)
    if not st or st.status != StockTakingStatus.DRAFT:
        raise ValueError("Invalid stock taking session")
        
    # Apply adjustments for all counted items
    for item in st.items:
        if item.counted_qty is None:
            continue # Skip uncounted? Or treat as 0? Usually skip in partial.
            
        diff = item.counted_qty - item.expected_qty
        if diff != 0:
            await create_stock_movement(
                session,
                variant_id=item.variant_id,
                warehouse_id=st.warehouse_id,
                qty_change=diff,
                reason=StockMovementReason.STOCK_TAKE,
                related_id=st.id
            )
            
    st.status = StockTakingStatus.COMPLETED
    st.completed_at = datetime.now().isoformat()
    await session.commit()
    return st

# ----------------------------------------------------------------------
# Transfer Request Service
# ----------------------------------------------------------------------

from app.modules.inventory.models import TransferRequest, TransferStatus
from app.modules.inventory.schemas import TransferRequestCreate, TransferRequestUpdate

async def get_transfer_requests(session: AsyncSession, limit: int = 50, offset: int = 0) -> List[TransferRequest]:
    stmt = (
        select(TransferRequest)
        .options(
            joinedload(TransferRequest.source_warehouse),
            joinedload(TransferRequest.destination_warehouse)
        )
        .order_by(TransferRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_transfer_request(session: AsyncSession, id: int) -> Optional[TransferRequest]:
    stmt = (
        select(TransferRequest)
        .where(TransferRequest.id == id)
        .options(
            joinedload(TransferRequest.source_warehouse),
            joinedload(TransferRequest.destination_warehouse)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_transfer_request(session: AsyncSession, data: TransferRequestCreate) -> TransferRequest:
    # Convert items list of models to list of dicts for JSON column
    items_data = [item.model_dump() for item in data.items]
    
    tr = TransferRequest(
        source_wh_id=data.source_wh_id,
        destination_wh_id=data.destination_wh_id,
        items=items_data,
        status=TransferStatus.DRAFT
    )
    session.add(tr)
    await session.commit()
    await session.refresh(tr)
    return tr

async def update_transfer_request(session: AsyncSession, id: int, data: TransferRequestUpdate) -> Optional[TransferRequest]:
    tr = await get_transfer_request(session, id)
    if not tr:
        return None
        
    # Check for status transition
    input_data = data.model_dump(exclude_unset=True)
    new_status = input_data.get('status')
    
    # Store old status to check transition logic
    old_status = tr.status
    
    if 'items' in input_data:
        # Convert items to dicts
        input_data['items'] = [item.model_dump() for item in input_data['items']]
        
    for key, value in input_data.items():
        setattr(tr, key, value)
        
    # Handle Status Transitions (Simple State Machine)
    # Draft -> Approved -> Shipped -> Received
    
    # 1. Shipped: Deduct from Source
    if new_status == TransferStatus.SHIPPED and old_status != TransferStatus.SHIPPED and old_status != TransferStatus.RECEIVED:
        for item in tr.items:
            await create_stock_movement(
                session, 
                variant_id=item['variant_id'], 
                warehouse_id=tr.source_wh_id, 
                qty_change=-item['qty'], 
                reason=StockMovementReason.TRANSFER,
                related_id=tr.id
            )
            
    # 2. Received: Add to Destination
    if new_status == TransferStatus.RECEIVED and old_status == TransferStatus.SHIPPED:
        for item in tr.items:
            await create_stock_movement(
                session, 
                variant_id=item['variant_id'], 
                warehouse_id=tr.destination_wh_id, 
                qty_change=item['qty'], 
                reason=StockMovementReason.TRANSFER,
                related_id=tr.id
            )
            
    session.add(tr)
    await session.commit()
    await session.refresh(tr)
    return tr
