import asyncio
from app.core.database import engine, Base
# Import all models to ensure they are registered with Base
from app.modules.settings.models import CheckoutConfig, GiftingConfig, InvoiceConfig

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_tables())
