import asyncio
import sys
import os
import requests
from datetime import datetime

sys.path.append(os.getcwd())
from database import AsyncSessionLocal, engine
from models import Base, Product, ProductVariant, Warehouse, InventoryItem, User
from auth_utils import create_access_token

# Helper to get auth token
def get_token():
    return create_access_token(data={"sub": "admin"})

async def verify_pos():
    print("Verifying POS System...")
    
    # Setup DB & Data
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Cleanup Old Data
        from sqlalchemy import text
        try:
            await session.execute(text("DELETE FROM stock_movements WHERE variant_id IN (SELECT id FROM product_variants WHERE sku = 'POS-001')"))
            await session.execute(text("DELETE FROM inventory_items WHERE variant_id IN (SELECT id FROM product_variants WHERE sku = 'POS-001')"))
            await session.execute(text("DELETE FROM order_items WHERE variant_id IN (SELECT id FROM product_variants WHERE sku = 'POS-001')"))
            await session.execute(text("DELETE FROM product_variants WHERE sku = 'POS-001'"))
            await session.execute(text("DELETE FROM products WHERE name = 'POS Item'"))
            await session.execute(text("DELETE FROM warehouses WHERE name = 'Main Store'"))
            await session.commit()
        except Exception:
            await session.rollback()

        # Create Main Warehouse
        wh = Warehouse(name="Main Store", location="Riyadh", priority_index=-100)
        session.add(wh)
        
        # Create Product & Variant
        p = Product(name="POS Item", product_type="physical")
        session.add(p)
        await session.commit()
        await session.refresh(p)
        
        v = ProductVariant(product_id=p.id, sku="POS-001", price=50.0)
        session.add(v)
        await session.commit()
        await session.refresh(v)
        await session.refresh(wh)
        
        # Initial Stock (10)
        inv = InventoryItem(variant_id=v.id, warehouse_id=wh.id, quantity=10)
        session.add(inv)
        await session.commit()
        
        var_id = v.id
        
    # --- TEST API ---
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://127.0.0.1:8000"
    
    # 1. Create Order via API (Simulate POS)
    payload = {
        "customer_id": None, # Guest
        "items": [
            {"variant_id": var_id, "quantity": 2} # Buy 2
        ],
        "payment_method": "card", # This might be ignored by our new logic which hardcodes 'multi' or accepts logic? 
        # Wait, my main.py create_order Logic sets `payment_method="multi"`.
        # So I will check that.
        "discount_detail": {}
    }
    
    print("\n1. Sending POS Order (Buy 2 units)...")
    try:
        r = requests.post(f"{base_url}/api/orders", json=payload, headers=headers)
        if r.status_code == 200:
            data = r.json()
            print(f" - Success: Order ID {data['id']}, Total: {data['total_amount']}")
        else:
            print(f" - Failed: {r.text}")
    except Exception as e:
        print(f" - Connection Error: {e}")
        return

    # 2. Check Z-Report
    print("\n2. Checking Z-Report...")
    try:
        r = requests.get(f"{base_url}/api/reports/z-report", headers=headers)
        if r.status_code == 200:
            rep = r.json()
            print(f" - Date: {rep['date']}")
            print(f" - Total Sales: {rep['total_sales']}")
            print(f" - Breakdown: {rep['breakdown']}")
            
            if rep['total_sales'] >= 100.0:
                 print(" - Z-Report VALID.")
            else:
                 print(" - Z-Report INVALID (Sales mismatch).")
        else:
            print(f" - Failed: {r.text}")
    except Exception as e:
        print(f" - Error: {e}")

    # 3. Verify Stock Deduction
    print("\n3. Verifying Stock Deduction...")
    session.expire_all()
    async with AsyncSessionLocal() as session: 
        from sqlalchemy import select
        stmt = select(InventoryItem).where(InventoryItem.variant_id == var_id, InventoryItem.warehouse_id == wh.id)
        res = await session.execute(stmt)
        item = res.scalar_one_or_none()
        
        if item and item.quantity == 8: # 10 - 2
            print(" - Stock Logic VALID (10 -> 8).")
        else:
            print(f" - Stock Logic FAILED. Qty: {item.quantity if item else 'None'}")

if __name__ == "__main__":
    asyncio.run(verify_pos())
