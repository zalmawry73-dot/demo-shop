
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List

from app.core.database import get_db
from app.dependencies import get_current_user
from app.modules.inventory.models import Product, ProductVariant, Warehouse, InventoryItem, StockMovement, StockMovementReason, Category, StockTaking
from app.modules.inventory.service import get_withdrawal_plan, create_stock_movement
from app.modules.auth.models import User

router = APIRouter(tags=["Inventory"])
templates = Jinja2Templates(directory="templates")

# Pages
@router.get("/inventory/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("inventory/dashboard.html", {"request": request})

# API
@router.get("/api/inventory")
async def get_inventory(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ProductVariant).options(joinedload(ProductVariant.product))
    result = await db.execute(stmt)
    variants = result.scalars().all()
    
    data = []
    for v in variants:
        # Get stock per warehouse
        stmt_stock = select(InventoryItem, Warehouse).join(Warehouse).where(InventoryItem.variant_id == v.id)
        res_stock = await db.execute(stmt_stock)
        stock_lines = res_stock.all()
        
        total = sum(item.quantity for item, _ in stock_lines)
        
        data.append({
            "id": v.id,
            "product_name": v.product.name,
            "sku": v.sku,
            "total_stock": total,
            "locations": [{"wh_id": wh.id, "wh": wh.name, "qty": item.quantity} for item, wh in stock_lines]
        })
    return data

@router.post("/api/move-stock")
async def move_stock(
    variant_id: str, 
    from_wh: int, 
    to_wh: int, 
    qty: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Deduction
    await create_stock_movement(db, variant_id, from_wh, -qty, StockMovementReason.TRANSFER)
    # Addition
    await create_stock_movement(db, variant_id, to_wh, qty, StockMovementReason.TRANSFER)
    return {"status": "success"}

# ----------------------------------------------------------------------
# Inventory Logs
# ----------------------------------------------------------------------

@router.get("/inventory/logs", response_class=HTMLResponse)
async def inventory_logs_page(request: Request):
    """Render the inventory logs page"""
    return templates.TemplateResponse("inventory/movements_list.html", {"request": request})

@router.get("/api/movements")
async def list_movements(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API to fetch movement history"""
    from app.modules.inventory.service import get_stock_movements
    movements = await get_stock_movements(db, limit, offset)
    
    data = []
    for m in movements:
        data.append({
            "id": m.id,
            "date": m.created_at.isoformat() if m.created_at else None,
            "product_name": m.variant.product.name if m.variant and m.variant.product else "Unknown",
            "sku": m.variant.sku if m.variant else "Unknown",
            "warehouse": m.warehouse.name if m.warehouse else "Unknown",
            "qty_change": m.qty_change,
            "reason": m.reason.value if m.reason else "Unknown",
            "user": "System" # Placeholder, ideally StockMovement has user_id
        })
    return data
    return data

# ----------------------------------------------------------------------
# Warehouse Management
# ----------------------------------------------------------------------

from app.modules.inventory.schemas import WarehouseCreate, WarehouseUpdate, WarehouseResponse, BatchInventoryUpdate
from app.modules.inventory.service import get_warehouses, create_warehouse, update_warehouse, batch_update_inventory, get_warehouse

@router.get("/inventory/warehouses", response_class=HTMLResponse)
async def warehouses_list_page(request: Request):
    """Page: List all warehouses"""
    return templates.TemplateResponse("inventory/warehouse_list.html", {"request": request})

@router.get("/inventory/warehouses/create", response_class=HTMLResponse)
async def warehouse_create_page(request: Request):
    """Page: Create new warehouse"""
    return templates.TemplateResponse("inventory/warehouse_form.html", {"request": request})

@router.get("/inventory/warehouses/{id}/edit", response_class=HTMLResponse)
async def warehouse_edit_page(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    """Page: Edit warehouse"""
    wh = await get_warehouse(db, id)
    if not wh: raise HTTPException(404, "Warehouse not found")
    return templates.TemplateResponse("inventory/warehouse_form.html", {"request": request, "warehouse": wh})

@router.get("/api/warehouses", response_model=List[WarehouseResponse])
async def list_warehouses_api(db: AsyncSession = Depends(get_db)):
    """API: Get all warehouses"""
    return await get_warehouses(db)

@router.post("/api/warehouses", response_model=WarehouseResponse)
async def create_warehouse_api(data: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    """API: Create warehouse"""
    return await create_warehouse(db, data)

@router.put("/api/warehouses/{id}", response_model=WarehouseResponse)
async def update_warehouse_api(id: int, data: WarehouseUpdate, db: AsyncSession = Depends(get_db)):
    """API: Update warehouse"""
    return await update_warehouse(db, id, data)

# ----------------------------------------------------------------------
# Batch Inventory Management
# ----------------------------------------------------------------------

@router.get("/inventory/management", response_class=HTMLResponse)
async def inventory_management_page(request: Request):
    """Page: Excel-like inventory grid"""
    return templates.TemplateResponse("inventory/bulk_editor.html", {"request": request})

@router.post("/api/inventory/batch-update")
async def batch_update_api(data: BatchInventoryUpdate, db: AsyncSession = Depends(get_db)):
    """API: Batch update stock"""
    try:
        await batch_update_inventory(db, data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(400, f"Batch update failed: {str(e)}")

# ----------------------------------------------------------------------
# Stock Taking (Audit)
# ----------------------------------------------------------------------

from app.modules.inventory.schemas import StockTakingCreate, StockTakingResponse, StockTakingItemUpdate
from app.modules.inventory.service import create_stock_taking, get_stock_taking, update_stock_taking_item, finalize_stock_taking

@router.get("/inventory/stock-taking", response_class=HTMLResponse)
async def stock_taking_list_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Page: List stock taking sessions"""
    try:
        stmt = select(StockTaking).options(joinedload(StockTaking.warehouse)).order_by(StockTaking.created_at.desc())
        res = await db.execute(stmt)
        items = res.scalars().all()
        return templates.TemplateResponse("inventory/stock_taking_list.html", {"request": request, "items": items})
    except Exception as e:
        import traceback
        return HTMLResponse(content=f"<pre>{traceback.format_exc()}</pre>", status_code=500)

@router.get("/inventory/stock-taking/create", response_class=HTMLResponse)
async def stock_taking_create_page(request: Request):
    """Page: Create new session"""
    return templates.TemplateResponse("inventory/stock_taking_form.html", {"request": request})

@router.get("/inventory/stock-taking/{id}", response_class=HTMLResponse)
async def stock_taking_detail_page(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    """Page: Perform stock taking"""
    st = await get_stock_taking(db, id)
    if not st: raise HTTPException(404)
    return templates.TemplateResponse("inventory/stock_taking_form.html", {"request": request, "stock_taking": st})

@router.post("/api/stock-taking", response_model=StockTakingResponse)
async def create_stock_taking_api(data: StockTakingCreate, db: AsyncSession = Depends(get_db)):
    return await create_stock_taking(db, data)

@router.post("/api/stock-taking/{id}/items")
async def update_item_api(id: int, data: StockTakingItemUpdate, db: AsyncSession = Depends(get_db)):
    await update_stock_taking_item(db, id, data.variant_id, data.counted_qty)
    return {"status": "success"}

@router.post("/api/stock-taking/{id}/finalize")
async def finalize_stock_taking_api(id: int, db: AsyncSession = Depends(get_db)):
    await finalize_stock_taking(db, id)
    return {"status": "success"}

# ----------------------------------------------------------------------
# Transfer Requests
# ----------------------------------------------------------------------

from app.modules.inventory.schemas import TransferRequestCreate, TransferRequestUpdate, TransferRequestResponse
from app.modules.inventory.service import get_transfer_requests, get_transfer_request, create_transfer_request, update_transfer_request

@router.get("/inventory/transfer-requests", response_class=HTMLResponse)
async def transfer_requests_list_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Page: List transfer requests"""
    try:
        requests = await get_transfer_requests(db)
        return templates.TemplateResponse("inventory/transfer_requests/list.html", {"request": request, "requests": requests})
    except Exception as e:
        import traceback
        return HTMLResponse(content=f"<pre>{traceback.format_exc()}</pre>", status_code=500)

@router.get("/inventory/transfer-requests/create", response_class=HTMLResponse)
async def transfer_request_create_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Page: Create transfer request"""
    warehouses = await get_warehouses(db)
    return templates.TemplateResponse("inventory/transfer_requests/create.html", {"request": request, "warehouses": warehouses})

@router.get("/inventory/transfer-requests/{id}", response_class=HTMLResponse)
async def transfer_request_detail_page(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    """Page: View/Edit transfer request"""
    tr = await get_transfer_request(db, id)
    if not tr: raise HTTPException(404, "Transfer Request not found")
    warehouses = await get_warehouses(db)
    
    # We might need product details for the items
    # For now, let's pass the raw items and handle enrichment in template or frontend fetch
    # Ideally we should enrich items with product names/skus here or in service
    
    # Quick enrichment for template
    # This is better done in service or via a separate API, but for MVP:
    enriched_items = []
    if tr.items:
        # Optimization: Batch fetch variants
        # For now, simplistic loop (N+1 danger if many items)
        for item in tr.items:
            # item is a dict with variant_id, qty
            stmt = select(ProductVariant).options(joinedload(ProductVariant.product)).where(ProductVariant.id == item['variant_id'])
            res = await db.execute(stmt)
            variant = res.scalar_one_or_none()
            enriched_items.append({
                "variant_id": item['variant_id'],
                "qty": item['qty'],
                "sku": variant.sku if variant else "Unknown",
                "product_name": variant.product.name if variant else "Unknown",
                "image_url": variant.product.images[0].image_url if variant and variant.product.images else "/static/images/placeholder.png"
            })
            
    return templates.TemplateResponse("inventory/transfer_requests/create.html", {
        "request": request, 
        "transfer_request": tr, 
        "warehouses": warehouses,
        "items": enriched_items
    })

@router.get("/api/transfer-requests", response_model=List[TransferRequestResponse])
async def list_transfer_requests_api(db: AsyncSession = Depends(get_db)):
    return await get_transfer_requests(db)

@router.post("/api/transfer-requests", response_model=TransferRequestResponse)
async def create_transfer_request_api(data: TransferRequestCreate, db: AsyncSession = Depends(get_db)):
    return await create_transfer_request(db, data)

@router.put("/api/transfer-requests/{id}", response_model=TransferRequestResponse)
async def update_transfer_request_api(id: int, data: TransferRequestUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_transfer_request(db, id, data)
    if not updated: raise HTTPException(404)
    return updated
