
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.schemas import OrderCreate, OrderResponse
from app.dependencies import get_current_user
from app.modules.sales.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from app.modules.customers.models import Customer
from app.modules.catalog.models import ProductVariant, Product
from app.modules.inventory.models import Warehouse, InventoryItem, StockMovement, StockMovementReason
from app.modules.auth.models import User
from app.modules.settings.service import ConfigurationService
from app.modules.sales.payment_service import PaymentService

from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import datetime
from app.modules.settings.notification_service import NotificationService, NotificationEventType

router = APIRouter(tags=["Sales"])
templates = Jinja2Templates(directory="templates")

@router.get("/pos")
async def pos_page(request: Request):
    return templates.TemplateResponse("pos.html", {"request": request})

@router.get("/api/pos/products")
async def get_pos_products(
    search: str = "", 
    category_id: str = "all", 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import joinedload, selectinload
    from app.modules.catalog.models import ProductImage
    
    stmt = (
        select(ProductVariant)
        .join(Product)
        .options(
            joinedload(ProductVariant.product)
            .selectinload(Product.images)
        )
    )
    
    if search:
        stmt = stmt.where(
            Product.name.ilike(f"%{search}%") | 
            ProductVariant.sku.ilike(f"%{search}%")
        )
    
    if category_id != "all":
        try:
             cid = int(category_id)
             stmt = stmt.where(Product.category_id == cid)
        except: 
            pass
        
    result = await db.execute(stmt)
    variants = result.unique().scalars().all()
    
    return [
        {
            "id": v.id,
            "name": v.product.name if v.product else "Unknown",
            "price": v.price,
            "image": (
                v.product.images[0].image_url 
                if v.product and v.product.images 
                else "/static/placeholder.png"
            )
        }
        for v in variants
    ]

# --- Calculation Schema ---
class CartItem(BaseModel):
    variant_id: str  # UUID string
    quantity: int

class CalculationRequest(BaseModel):
    items: List[CartItem]
    city: str = ""

@router.post("/api/orders/calculate")
async def calculate_order(
    req: CalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subtotal = 0.0
    total_weight = 0.0
    
    # 1. Calculate Items Total & Weight
    for item in req.items:
        from sqlalchemy.orm import joinedload
        
        stmt = (
            select(ProductVariant)
            .join(Product)
            .where(ProductVariant.id == item.variant_id)
            .options(joinedload(ProductVariant.product))
        )
        res = await db.execute(stmt)
        variant = res.unique().scalar_one_or_none()
        if not variant: 
            continue
        
        subtotal += variant.price * item.quantity
        if variant.product and variant.product.weight:
            total_weight += variant.product.weight * item.quantity
            
    # 2. Shipping & Tax
    settings = await ConfigurationService.get_settings(db)
    shipping_cost = await ConfigurationService.calculate_shipping(db, subtotal, total_weight)
    
    taxable_base = subtotal + shipping_cost
    tax_res = ConfigurationService.calculate_tax(taxable_base, settings)
    
    total = taxable_base
    if not settings.tax_inclusive:
        total += tax_res['tax_amount']
        
    return {
        "subtotal": subtotal,
        "shipping": shipping_cost,
        "tax": tax_res['tax_amount'],
        "total": total,
        "weight": total_weight
    }

@router.post("/api/orders", response_model=OrderResponse)
async def create_order(
    request: Request,
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Includes Checkout Logic (Tax, Shipping etc) migrated from old main.py
    
    # 1. Customer
    customer = None
    if order.customer_id:
        result = await db.execute(select(Customer).where(Customer.id == order.customer_id))
        customer = result.scalar_one_or_none()
    
    if not customer:
        customer = Customer(name="Guest", email=f"guest_order_{order.items[0].variant_id}@store.com") # Simplified
        db.add(customer)
        await db.commit()
    
    # 2. Setup Order
    new_order = Order(
        customer_id=customer.id,
        status=OrderStatus.NEW,
        payment_status="pending",
        payment_method="multi",
        payment_details=order.payment_details or {},
        total_amount=0.0
    )
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    subtotal = 0.0
    total_weight = 0.0
    
    # 3. Items
    for item in order.items:
        stmt = select(ProductVariant, Product).join(Product).where(ProductVariant.id == item.variant_id)
        res = await db.execute(stmt)
        row = res.first()
        if not row: continue
        variant, product = row
        
        if product.weight:
            total_weight += product.weight * item.quantity
            
        # Add Item
        db.add(OrderItem(order_id=new_order.id, variant_id=variant.id, quantity=item.quantity, unit_price=variant.price))
        subtotal += variant.price * item.quantity
    
    # Validate Constraints BEFORE deducting stock
    from app.modules.settings.constraints_validator import ConstraintsValidator
    
    # Collect product IDs from order
    product_ids = [item.variant_id for item in order.items]
    
    # Validate shipping constraints if shipping company is specified
    if order.shipping_company:
        shipping_validation = await ConstraintsValidator.validate_shipping_constraints(
            db=db,
            shipping_company_id=order.shipping_company,
            cart_total=subtotal,
            product_ids=product_ids
        )
        if not shipping_validation["allowed"]:
            raise HTTPException(status_code=400, detail=shipping_validation["error_message"])
    
    
    # Validate payment constraints (only if payment_method is numeric ID)
    # For simple methods like "cod", "transfer" we skip constraint validation
    if order.payment_method and isinstance(order.payment_method, int):
        payment_validation = await ConstraintsValidator.validate_payment_constraints(
            db=db,
            payment_method_id=order.payment_method,
            cart_total=subtotal,
            product_ids=product_ids
        )
        if not payment_validation["allowed"]:
            raise HTTPException(status_code=400, detail=payment_validation["error_message"])
    
    # Now deduct stock (after validation passes)
    for item in order.items:
        stmt = select(ProductVariant, Product).join(Product).where(ProductVariant.id == item.variant_id)
        res = await db.execute(stmt)
        row = res.first()
        if not row: continue
        variant, product = row
        
        # Deduct Stock (Main Implementation)
        stmt_wh = select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.priority_index.asc()).limit(1)
        res_wh = await db.execute(stmt_wh)
        wh = res_wh.scalar_one_or_none()
        
        if wh:
            inv_stmt = select(InventoryItem).where(InventoryItem.variant_id == variant.id, InventoryItem.warehouse_id == wh.id)
            inv_res = await db.execute(inv_stmt)
            inv_item = inv_res.scalar_one_or_none()
            
            # STRICT VALIDATION
            current_qty = inv_item.quantity if inv_item else 0
            if current_qty < item.quantity:
                # Rollback handled by FastAPI dependency exception usually, but explicit here is safer if we committed earlier
                # However, for this simplified flow, we raise error. 
                # Ideally check all stock BEFORE creating order. For now, we assume check passed in UI or we fail here.
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name} ({variant.sku}). Available: {current_qty}")

            if inv_item: inv_item.quantity -= item.quantity
            else: db.add(InventoryItem(variant_id=variant.id, warehouse_id=wh.id, quantity=-item.quantity))
            
            db.add(StockMovement(variant_id=variant.id, warehouse_id=wh.id, qty_change=-item.quantity, reason=StockMovementReason.NEW_ORDER, related_id=new_order.id))

    # 4. Settings Apply
    settings = await ConfigurationService.get_settings(db)
    shipping_cost = await ConfigurationService.calculate_shipping(db, subtotal, total_weight)
    
    taxable_base = subtotal + shipping_cost
    tax_res = ConfigurationService.calculate_tax(taxable_base, settings)
    
    new_order.shipping_cost = shipping_cost
    new_order.tax_amount = tax_res['tax_amount']
    
    if settings.tax_inclusive:
        new_order.total_amount = taxable_base
    else:
        new_order.total_amount = taxable_base + tax_res['tax_amount']
        
    new_order.status = OrderStatus.COMPLETED
    new_order.payment_status = "paid"
    
    # 5. History Log
    history_entry = OrderStatusHistory(
        order_id=new_order.id,
        old_status=None,
        new_status=new_order.status.value,
        changed_by=current_user.email if current_user else "System",
        created_at=datetime.datetime.now().isoformat()
    )
    db.add(history_entry)
    
    await db.commit()
    await db.commit()
    await db.commit()
    
    # 6. Notifications
    try:
        # Refresh order with customer relationship loaded to avoid "MissingGreenlet" or hangs
        stmt = select(Order).options(selectinload(Order.customer)).where(Order.id == new_order.id)
        result = await db.execute(stmt)
        order_with_rels = result.scalar_one()
        
        await NotificationService.send_notification(db, order_with_rels, NotificationEventType.ORDER_CREATED)
    except Exception as e:
        print(f"Failed to send notification: {e}")
        
    return OrderResponse(id=new_order.id, status=new_order.status, total_amount=new_order.total_amount)

# --- Management Endpoints ---

@router.get("/orders")
async def orders_page(request: Request):
    return templates.TemplateResponse("orders/list.html", {"request": request})

@router.get("/orders/drafts")
async def drafts_page(request: Request):
    return templates.TemplateResponse("orders/drafts.html", {"request": request})

@router.get("/orders/abandoned")
async def abandoned_page(request: Request):
    return templates.TemplateResponse("orders/abandoned.html", {"request": request})

@router.get("/orders/{order_id}")
async def order_details_page(request: Request, order_id: int):
    return templates.TemplateResponse("orders/details.html", {"request": request, "order_id": order_id})

@router.get("/api/orders_list")
async def list_orders(
    page: int = 1,
    limit: int = 10,
    status: str = "all",
    payment_status: str = "all",
    date_from: str = None,
    date_to: str = None,
    search: str = None,
    sort: str = "newest",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    response: Request = None # To set headers
):
    offset = (page - 1) * limit
    
    # Base Query
    stmt = select(Order).join(Customer).options(selectinload(Order.customer), selectinload(Order.items))
    
    # Filters
    if status and status != "all":
        stmt = stmt.where(Order.status == status)
        
    if payment_status and payment_status != "all":
        stmt = stmt.where(Order.payment_status == payment_status)

    if date_from:
         stmt = stmt.where(Order.created_at >= date_from)
         
    if date_to:
         stmt = stmt.where(Order.created_at <= date_to)

    if search:
        # Search ID or Customer Name
        if search.isdigit():
            stmt = stmt.where(Order.id == int(search))
        else:
            stmt = stmt.where(Customer.name.ilike(f"%{search}%"))
            
    # Sorting
    if sort == "newest":
        stmt = stmt.order_by(Order.created_at.desc())
    elif sort == "oldest":
        stmt = stmt.order_by(Order.created_at.asc())
    elif sort == "total_high":
        stmt = stmt.order_by(Order.total_amount.desc())
    elif sort == "total_low":
        stmt = stmt.order_by(Order.total_amount.asc())

    # Count Query (Simplified)
    # Ideally should run a separate count query or use window functions
    # For now, we fetch all to count then slice (Not optimized for huge data, but fits prototype scope)
    # Optimization: Use `func.count` separately.
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_res = await db.execute(count_stmt)
    total_count = count_res.scalar()
    
    # Apply Pagination
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    # Return with metadata (using dict to include meta, or headers)
    return {
        "data": [
            {
                "id": o.id,
                "customer": o.customer.name if o.customer else "Unknown",
                "customer_phone": o.customer.mobile if o.customer else "",
                "date": o.created_at.strftime("%Y-%m-%d %H:%M"),
                "date_human": o.created_at.strftime("%Y-%m-%d"), # Could use humanize lib
                "status": o.status.value,
                "total": o.total_amount,
                "payment_status": o.payment_status,
                "payment_method": o.payment_method,
                "items_count": len(o.items)
            }
            for o in orders
        ],
        "meta": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count + limit - 1) // limit
        }
    }

from sqlalchemy.orm import selectinload

@router.get("/api/orders/{order_id}/details")
async def get_order_details(order_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product),
        selectinload(Order.customer)
    ).where(Order.id == order_id)
    
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    
    if not order: raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": order.id,
        "date": order.created_at.isoformat(),
        "status": order.status.value,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "customer": {
            "name": order.customer.name,
            "email": order.customer.email,
            "phone": order.customer.mobile
        },
        "items": [
            {
                "name": item.variant.product.name,
                "variant": item.variant.sku,
                "qty": item.quantity,
                "price": item.unit_price,
                "total": item.quantity * item.unit_price,
                "image": item.variant.product.images[0].image_url if item.variant.product.images else ""
            }
            for item in order.items
        ],
        "subtotal": sum(i.quantity * i.unit_price for i in order.items),
        "tax": order.tax_amount,
        "shipping": order.shipping_cost,
        "total": order.total_amount
    }

from pydantic import BaseModel
class StatusUpdate(BaseModel):
    status: str

@router.patch("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, update: StatusUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Fetch order with items
    stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order: raise HTTPException(404)
    
    old_status = order.status.value
    order.status = update.status
    
    # Handle stock return for cancelled orders
    if update.status == "cancelled":
        from app.modules.settings.models import ProductSettings
        
        # Check if return_cancelled_quantity is enabled
        product_settings_stmt = select(ProductSettings).limit(1)
        ps_result = await db.execute(product_settings_stmt)
        product_settings = ps_result.scalar_one_or_none()
        
        if product_settings and product_settings.return_cancelled_quantity:
            # Return stock to inventory
            for item in order.items:
                stmt_wh = select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.priority_index.asc()).limit(1)
                res_wh = await db.execute(stmt_wh)
                wh = res_wh.scalar_one_or_none()
                
                if wh:
                    inv_stmt = select(InventoryItem).where(
                        InventoryItem.variant_id == item.variant_id,
                        InventoryItem.warehouse_id == wh.id
                    )
                    inv_res = await db.execute(inv_stmt)
                    inv_item = inv_res.scalar_one_or_none()
                    
                    if inv_item:
                        inv_item.quantity += item.quantity
                    else:
                        db.add(InventoryItem(variant_id=item.variant_id, warehouse_id=wh.id, quantity=item.quantity))
                    
                    # Log stock movement
                    db.add(StockMovement(
                        variant_id=item.variant_id,
                        warehouse_id=wh.id,
                        qty_change=item.quantity,
                        reason=StockMovementReason.ORDER_CANCELLED,
                        related_id=order.id
                    ))
    
    # Add History
    history = OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=update.status,
        changed_by=current_user.email if current_user else "System",
        created_at=datetime.datetime.now().isoformat()
    )
    db.add(history)
    
    await db.commit()
    
    # Customer Notifications
    try:
        event_map = {
            "new": NotificationEventType.ORDER_CREATED,
            "processing": NotificationEventType.ORDER_PROCESSING,
            "ready": NotificationEventType.ORDER_READY,
            "shipping": NotificationEventType.ORDER_SHIPPED,
            "completed": NotificationEventType.ORDER_COMPLETED,
            "cancelled": NotificationEventType.ORDER_CANCELLED
        }
        
        event = event_map.get(update.status)
        if event:
            # Re-fetch with customer explicitly
            stmt = select(Order).options(selectinload(Order.customer)).where(Order.id == order_id)
            res = await db.execute(stmt)
            order_full = res.scalar_one()
            
            await NotificationService.send_notification(db, order_full, event)
            
    except Exception as e:
        print(f"Failed to send customer notification: {e}")
    
    # Staff Notifications
    try:
        from app.modules.settings.models import StoreSettings
        
        settings_stmt = select(StoreSettings).limit(1)
        settings_result = await db.execute(settings_stmt)
        store_settings = settings_result.scalar_one_or_none()
        
        if store_settings and store_settings.staff_notifications:
            status_key = update.status.replace("_", "")  # convert "pending_payment" to "pendingpayment"
            # Check simple mapping
            if update.status == "new" and store_settings.staff_notifications.get("new"):
                await NotificationService.send_staff_notification(db, order, "new", store_settings)
            elif update.status == "processing" and store_settings.staff_notifications.get("processing"):
                await NotificationService.send_staff_notification(db, order, "processing", store_settings)
            elif update.status == "ready" and store_settings.staff_notifications.get("ready"):
                await NotificationService.send_staff_notification(db, order, "ready", store_settings)
            elif update.status == "shipping" and store_settings.staff_notifications.get("delivering"):
                await NotificationService.send_staff_notification(db, order, "delivering", store_settings)
            elif update.status == "completed" and store_settings.staff_notifications.get("completed"):
                await NotificationService.send_staff_notification(db, order, "completed", store_settings)
            elif update.status == "cancelled" and store_settings.staff_notifications.get("cancelled"):
                await NotificationService.send_staff_notification(db, order, "cancelled", store_settings)
                
    except Exception as e:
        print(f"Failed to send staff notification: {e}")
        
    return {"status": "updated"}

# --- Export ---
import pandas as pd
from fastapi.responses import StreamingResponse
import io

@router.get("/api/orders/export/excel")
async def export_orders_excel(db: AsyncSession = Depends(get_db)):
    stmt = select(Order).join(Customer).order_by(Order.created_at.desc())
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    data = []
    for o in orders:
        data.append({
            "Order ID": o.id,
            "Date": o.created_at,
            "Customer": o.customer.name,
            "Status": o.status.value,
            "Payment": o.payment_status,
            "Total": o.total_amount
        })
        
    df = pd.DataFrame(data)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream) as writer:
        df.to_excel(writer, index=False)
    
    stream.seek(0)
    
    return StreamingResponse(
        stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=orders_export.xlsx"}
    )
