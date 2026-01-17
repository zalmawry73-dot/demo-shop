import asyncio
import sys
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.inventory.models import StockTaking, Warehouse, StockTakingItem
from app.modules.catalog.models import Product, ProductVariant

async def test_query():
    print("Starting debug query...")
    async with AsyncSessionLocal() as session:
        try:
            print("Querying StockTakings...")
            stmt = select(StockTaking).join(Warehouse).order_by(StockTaking.created_at.desc())
            result = await session.execute(stmt)
            items = result.scalars().all()
            print(f"Success! Found {len(items)} items.")
            for item in items:
                print(f"- {item.name} ({item.status})")
        except Exception as e:
            print("Error during query execution!")
            print(e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_query())
