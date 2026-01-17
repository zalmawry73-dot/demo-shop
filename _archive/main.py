from fastapi import FastAPI, Depends, HTTPException, Body, status, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import csv
import io

from database import get_db, engine, AsyncSessionLocal
from models import Base, Order, OrderStatus, Analytics, User, Warehouse, InventoryItem, ProductVariant, Product, StockMovement, StockMovementReason, OrderItem, Customer, StoreSettings, PaymentConfig, ShippingRule, BranchType
from auth_utils import create_access_token, get_current_user, get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from schemas import OrderCreate, OrderResponse
from settings_service import ConfigurationService

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create Default Admin User
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar():
            hashed_pw = get_password_hash("secret")
            admin_user = User(username="admin", email="admin@store.com", password_hash=hashed_pw, role="admin")
            session.add(admin_user)
            await session.commit()
            print("Admin user created: admin / secret")

# --- Pages Routes ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request):
    return templates.TemplateResponse("inventory.html", {"request": request})

@app.get("/pos", response_class=HTMLResponse)
async def pos_page(request: Request):
    return templates.TemplateResponse("pos.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")

# --- Reports ---
@app.get("/api/reports/z-report")
async def get_z_report(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Returns total sales for the current day, broken down by payment status/method if available.
    For this prototype, we group by 'payment_method'.
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Total Sales Today
    stmt = (
        select(func.sum(Order.total_amount))
        .where(Order.created_at >= today_start, Order.status == OrderStatus.COMPLETED)
    )
    result = await db.execute(stmt)
    total_sales = result.scalar() or 0.0

    # 2. Total Count
    stmt_count = (
        select(func.count(Order.id))
        .where(Order.created_at >= today_start, Order.status == OrderStatus.COMPLETED)
    )
    result_count = await db.execute(stmt_count)
    total_orders = result_count.scalar() or 0

    # 3. Breakdown by Method (Simulated since we just added the column and it might be 'multi' or 'card')
    # In a real Z-Report, we'd parse the 'payment_details' JSON or rely on 'payment_method' column if it stores primary.
    # We'll group by payment_method column.
    stmt_breakdown = (
        select(Order.payment_method, func.sum(Order.total_amount))
        .where(Order.created_at >= today_start, Order.status == OrderStatus.COMPLETED)
        .group_by(Order.payment_method)
    )
    result_br = await db.execute(stmt_breakdown)
    breakdown = [{"method": row[0], "total": row[1] or 0.0} for row in result_br.all()]

    return {
        "date": today_start.strftime("%Y-%m-%d"),
        "total_sales": total_sales,
        "total_orders": total_orders,
        "breakdown": breakdown
    }

from fastapi.responses import RedirectResponse

# --- API Endpoints ---
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # ... [Same as before] ...
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/reports/sales-chart")
async def get_sales_chart_data(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    """
    Groups Completed Orders by Date for the chart.
    """
    # SQLite date handling can be tricky, using simple date extraction
    # This query groups by day locally or via DB
    stmt = (
        select(func.date(Order.created_at).label("day"), func.sum(Order.total_amount).label("total"))
        .where(Order.status == OrderStatus.COMPLETED)
        .group_by(func.date(Order.created_at))
        .order_by("day")
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    labels = []
    data = []
    
    for row in rows:
        labels.append(row.day)
        data.append(row.total)
    
    # Validation data if empty
    if not labels:
        labels = [date.today().strftime("%Y-%m-%d")]
        data = [0]

    return {"labels": labels, "data": data}

@app.get("/api/warehouses")
async def get_warehouses(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    stmt = select(Warehouse).order_by(Warehouse.priority_index.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@app.post("/api/warehouses/priority")
async def update_warehouse_priority(
    priority_data: Dict[str, List[int]] = Body(...), 
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    ids_order = priority_data.get("order", [])
    if not ids_order:
        raise HTTPException(status_code=400, detail="Order list is empty")
        
    for index, wh_id in enumerate(ids_order):
        stmt = update(Warehouse).where(Warehouse.id == wh_id).values(priority_index=index)
        await db.execute(stmt)
        
    await db.commit()
    return {"status": "success", "message": "Priorities updated"}

@app.post("/api/orders", response_model=OrderResponse)
async def create_order(
    request: Request,
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Lookup Customer
    customer = None
    if order.customer_id:
        result = await db.execute(select(Customer).where(Customer.id == order.customer_id))
        customer = result.scalar_one_or_none()
        
    if not customer:
        # Create Guest Customer if not exists
        customer = Customer(name="Guest", email=f"guest_{datetime.utcnow().timestamp()}@store.com")
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

    # 1. Create Order
    new_order = Order(
        customer_id=customer.id,
        status=OrderStatus.NEW,
        payment_status="pending",
        payment_method=order.payment_method or "multi",
        total_amount=0.0,
        is_draft=False,
        discount_detail=order.discount_detail if hasattr(order, 'discount_detail') else {}
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    subtotal = 0.0
    total_weight = 0.0

    # 2. Add Items & Deduct Stock
    for item in order.items:
        # Fetch Variant & Product for Weight
        stmt = select(ProductVariant, Product).join(Product).where(ProductVariant.id == item.variant_id)
        result = await db.execute(stmt)
        row = result.first()
        
        if not row: continue
        variant, product = row
        
        # Calculate Weight (if available)
        if product.weight:
            total_weight += product.weight * item.quantity

        # Inventory Logic (Dynamic Warehouse)
        stmt_wh = select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.priority_index.asc()).limit(1)
        res_wh = await db.execute(stmt_wh)
        default_wh = res_wh.scalar_one_or_none()
        if not default_wh: raise HTTPException(status_code=500, detail="No active warehouse")
        wh_id = default_wh.id
        
        # Deduct Stock
        inv_stmt = select(InventoryItem).where(InventoryItem.variant_id == variant.id, InventoryItem.warehouse_id == wh_id)
        inv_res = await db.execute(inv_stmt)
        inv_item = inv_res.scalar_one_or_none()
        
        if inv_item: inv_item.quantity -= item.quantity
        else: db.add(InventoryItem(variant_id=variant.id, warehouse_id=wh_id, quantity=-item.quantity))
        
        # Log Movement
        db.add(StockMovement(
            variant_id=variant.id, warehouse_id=wh_id, qty_change=-item.quantity,
            reason=StockMovementReason.NEW_ORDER, related_id=new_order.id
        ))

        # Add Order Item
        db.add(OrderItem(
            order_id=new_order.id, variant_id=variant.id, quantity=item.quantity, unit_price=variant.price
        ))
        
        subtotal += variant.price * item.quantity

    # 3. Calculations (Shipping & Tax)
    # Get Settings
    settings = await ConfigurationService.get_settings(db)
    
    # Calculate Shipping
    shipping_cost = await ConfigurationService.calculate_shipping(db, subtotal, total_weight, zone="All")
    
    # Calculate Tax (on Subtotal + Shipping usually, or just Subtotal depending on law. Here Subtotal + Shipping)
    taxable_base = subtotal + shipping_cost
    tax_res = ConfigurationService.calculate_tax(taxable_base, settings)
    
    new_order.shipping_cost = shipping_cost
    new_order.tax_amount = tax_res['tax_amount']
    # If inclusive, total is just taxable_base (which was sub + ship). If exclusive, add tax.
    if settings.tax_inclusive:
         new_order.total_amount = taxable_base
    else:
         new_order.total_amount = taxable_base + tax_res['tax_amount']

    # 4. Payment Processing (if POS/Online)
    # If online payment method selected (e.g. Stripe), try to process.
    # For POS 'multi' or 'cash', we assume paid.
    if new_order.payment_method in ['stripe', 'cc']: 
        # Import here to avoid circular
        from payment_service import PaymentService
        # Mock payment details passed in payload?
        payment_res = await PaymentService.process_order_payment(db, new_order, new_order.payment_method, {})
        if payment_res.get('status') == 'success':
            new_order.status = OrderStatus.COMPLETED
            new_order.payment_status = 'paid'
        else:
            new_order.status = OrderStatus.PENDING_PAYMENT
            new_order.payment_status = 'failed'
    else:
        # manual/pos default
        new_order.status = OrderStatus.COMPLETED
        new_order.payment_status = 'paid'

    await db.commit()
    await db.refresh(new_order)
    
    return OrderResponse(id=new_order.id, status=new_order.status, total_amount=new_order.total_amount)
    
    await db.commit()
    await db.refresh(new_order)
    
    return OrderResponse(id=new_order.id, status=new_order.status, total_amount=total_amount)

@app.get("/api/inventory/export")
async def export_stock_sheet(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    # ... [Same as before] ...
    stmt = (
        select(
            Product.name,
            ProductVariant.sku,
            Warehouse.name.label("warehouse_name"),
            InventoryItem.quantity
        )
        .select_from(InventoryItem)
        .join(ProductVariant)
        .join(Warehouse)
        .join(ProductVariant.product)
        .order_by(Product.name, Warehouse.name)
    )
    result = await db.execute(stmt)
    rows = result.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product Name", "SKU", "Warehouse", "System Qty", "Physical Count"])
    for row in rows:
        writer.writerow([row.name, row.sku, row.warehouse_name, row.quantity, ""])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_sheet.csv"}
    )

@app.get("/api/pos/products")
async def get_pos_products(
    search: str = None, 
    category_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Returns a flat list of variants for the POS Grid.
    """
    stmt = (
        select(ProductVariant, Product)
        .join(Product)
        .order_by(Product.name)
    )
    
    if search:
        # Search by Name, SKU, or Barcode
        term = f"%{search}%"
        stmt = stmt.where(
            (Product.name.ilike(term)) |
            (ProductVariant.sku.ilike(term)) |
            (ProductVariant.barcode == search)
        )
        
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)

    result = await db.execute(stmt)
    rows = result.all()
    
    products = []
    for variant, product in rows:
        products.append({
            "id": variant.id,
            "name": f"{product.name} {'(' + variant.sku + ')' if variant.sku else ''}",
            "price": variant.price,
            "image": "IMG", # Placeholder, would join ProductImage in real app
            "category_id": product.category_id
        })
        
    return products

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    # ... [Same as before] ...
    stmt_sales = select(func.sum(Order.total_amount)).where(Order.status == OrderStatus.COMPLETED)
    result_sales = await db.execute(stmt_sales)
    total_sales = result_sales.scalar() or 0.0

    stmt_count = select(func.count(Order.id))
    result_count = await db.execute(stmt_count)
    orders_count = result_count.scalar() or 0

    stmt_visits = select(func.sum(Analytics.visits)) 
    result_visits = await db.execute(stmt_visits)
    visits_count = result_visits.scalar() or 0

    conversion_rate = 0.0
    if visits_count > 0:
        conversion_rate = (orders_count / visits_count) * 100

    return {
        "total_sales": total_sales,
        "orders_count": orders_count,
        "visits_count": visits_count,
        "conversion_rate": round(conversion_rate, 2)
    }

@app.get("/api/dashboard/recent-orders")
async def get_recent_orders(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload
    stmt = (
        select(Order)
        .options(selectinload(Order.customer))
        .order_by(desc(Order.created_at))
        .limit(5)
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()
    response_data = []
    for order in orders:
        response_data.append({
            "order_id": order.id,
            "customer_name": order.customer.name if order.customer else "Unknown",
            "date": order.created_at.strftime("%Y-%m-%d"),
            "status": order.status.value,
            "total_amount": order.total_amount
        })
    return response_data
