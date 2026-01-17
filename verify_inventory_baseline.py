
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.catalog.models import Product, ProductVariant
from app.modules.inventory.models import InventoryItem

# Import all routers to trigger model registration
from app.modules.auth import routes as auth_routes
from app.modules.inventory import routes as inventory_routes
from app.modules.sales import routes as sales_routes
from app.modules.customers import routes as customers_routes
from app.modules.marketing import routes as marketing_routes

async def check_baseline():
    async with AsyncSessionLocal() as db:
        # Find a product with variants (limit 1)
        # We join to ensure it has variants
        stmt = select(Product).join(ProductVariant).limit(1)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if not product:
            print("No testable products found (must have variants).")
            return

        print(f"Test Product: {product.name} (ID: {product.id})")
        
        # Get Variants and Inventory
        stmt = select(ProductVariant).where(ProductVariant.product_id == product.id)
        res = await db.execute(stmt)
        variants = res.scalars().all()
        
        for v in variants:
            # Check Inventory
            inv_stmt = select(InventoryItem).where(InventoryItem.variant_id == v.id)
            inv_res = await db.execute(inv_stmt)
            inv = inv_res.scalar_one_or_none()
            qty = inv.quantity if inv else 0
            print(f"  - Variant: {v.sku} (ID: {v.id}) | Price: {v.price} | Stock: {qty}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_baseline())
