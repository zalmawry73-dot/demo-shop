
import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.modules.catalog.models import Product, ProductVariant, Category
from app.modules.inventory.models import InventoryItem, Warehouse

# Trigger registration
from app.modules.auth import routes as auth_routes
from app.modules.inventory import routes as inventory_routes
from app.modules.sales import routes as sales_routes
from app.modules.customers import routes as customers_routes
from app.modules.marketing import routes as marketing_routes


async def seed_data():
    async with AsyncSessionLocal() as db:
        print("Seeding Test Data...")
        
        # 1. Product
        product_id = str(uuid.uuid4())
        product = Product(
            id=product_id,
            name="Test Smartphone",
            description="A test product for E2E verification",
            product_type="Physical",
            status="Active",
            slug=f"test-smartphone-{uuid.uuid4().hex[:6]}"
        )
        db.add(product)
        
        # 2. Variant
        variant_id = str(uuid.uuid4())
        sku = f"TEST-PHONE-{uuid.uuid4().hex[:4].upper()}"
        variant = ProductVariant(
            id=variant_id,
            product_id=product_id,
            sku=sku,
            price=100.0,
            quantity=0, # Denormalized field, but main source is InventoryItem
            options='{"Color": "Black"}'
        )
        db.add(variant)
        
        # 2.5 Warehouse
        warehouse = Warehouse(
            name="Main Warehouse",
            location="HQ",
            branch_type="warehouse"
        )
        db.add(warehouse)
        await db.flush() # Get ID
        
        # 3. Inventory
        inv = InventoryItem(
            variant_id=variant_id,
            warehouse_id=warehouse.id,
            quantity=10
        )
        db.add(inv)
        
        await db.commit()
        
        print("SUCCESS!")
        print(f"Product ID: {product_id}")
        print(f"Variant ID: {variant_id}")
        print(f"SKU: {sku}")
        print(f"Initial Stock: 10")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(seed_data())
