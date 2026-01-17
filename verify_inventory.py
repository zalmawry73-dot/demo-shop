import asyncio
import sys
import os

sys.path.append(os.getcwd())

from models import Base, Warehouse, Product, ProductVariant, InventoryItem, StockMovementReason
from database import engine, AsyncSessionLocal
from inventory_service import get_withdrawal_plan, create_stock_movement

async def verify_inventory_logic():
    async with AsyncSessionLocal() as session:
        # 1. Setup Data
        print("Setting up inventory data...")
        
        # Create Warehouses
        wh1 = Warehouse(name="WH Riyadh", location="Riyadh", priority_index=0)
        wh2 = Warehouse(name="WH Jeddah", location="Jeddah", priority_index=1)
        wh3 = Warehouse(name="WH Dammam", location="Dammam", priority_index=2)
        session.add_all([wh1, wh2, wh3])
        await session.flush()
        
        # Create Product & Variant
        prod = Product(name="Test Item", product_type="physical")
        session.add(prod)
        await session.flush()
        
        variant = ProductVariant(product_id=prod.id, sku="TEST-INV-001", price=100.0)
        session.add(variant)
        await session.flush()
        
        # Add Inventory
        # WH1: 5 units
        await create_stock_movement(session, variant.id, wh1.id, 5, StockMovementReason.STOCK_TAKE)
        # WH2: 10 units
        await create_stock_movement(session, variant.id, wh2.id, 10, StockMovementReason.STOCK_TAKE)
        # WH3: 20 units
        await create_stock_movement(session, variant.id, wh3.id, 20, StockMovementReason.STOCK_TAKE)
        
        print(f"Initial Stock: WH1={5}, WH2={10}, WH3={20}")
        
        # 2. Test Withdrawal Algo
        # Request 12 Units
        # Expected: 5 from WH1, 7 from WH2, 0 from WH3
        print("\nRequesting 12 units...")
        plan = await get_withdrawal_plan(session, variant.id, 12)
        
        print("Withdrawal Plan:")
        for step in plan:
            print(f" - Warehouse: {step['warehouse_name']} (ID: {step['warehouse_id']}), Take: {step['take_qty']}")
            
        # Verify Plan
        assert len(plan) == 2
        assert plan[0]['warehouse_id'] == wh1.id and plan[0]['take_qty'] == 5
        assert plan[1]['warehouse_id'] == wh2.id and plan[1]['take_qty'] == 7
        print("SUCCESS: Plan matches expected logic!")

if __name__ == "__main__":
    async def run():
        # Re-init DB to include new models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        await verify_inventory_logic()
        
    asyncio.run(run())
