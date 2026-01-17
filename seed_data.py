
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.database import DATABASE_URL
from app.modules.inventory.models import InventoryItem, Warehouse
from app.modules.catalog.models import Category, Product, ProductVariant, ProductTypeEnum as ProductType
from app.modules.customers.models import Customer
# Import A LL modules to ensure SQLAlchemy Configures Relationships correctly
import app.modules.marketing.models
import app.modules.auth.models
import app.modules.settings.models
import app.modules.sales.models
import app.modules.inventory.models

async def seed_demo_data():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Seeding Demo Data...")

        # 1. Ensure Warehouse exists
        stmt = select(Warehouse).limit(1)
        res = await session.execute(stmt)
        wh = res.scalar_one_or_none()
        if not wh:
            print("Error: Main Warehouse not found. Run reset_db.py first.")
            # For this task, we can continue even if warehouse is missing, or return
            # But let's add Admin User here
        
        # 1.5 Admin User
        from app.modules.auth.models import User, UserRole, SecuritySettings
        from app.core.security import get_password_hash
        
        stmt = select(User).where(User.username == "admin")
        res = await session.execute(stmt)
        admin_user = res.scalar_one_or_none()
        
        if not admin_user:
            print("Creating Admin User...")
            admin_user = User(
                username="admin",
                email="admin@store.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                full_name="System Administrator",
                is_active=True,
                token_version=1
            )
            # Add default security settings
            admin_user.security_settings = SecuritySettings()
            
            session.add(admin_user)
            await session.flush()
        else:
             # Ensure admin has security settings if they exist but were created without them (e.g. old seed)
            stmt_ss = select(SecuritySettings).where(SecuritySettings.user_id == admin_user.id)
            res_ss = await session.execute(stmt_ss)
            ss = res_ss.scalar_one_or_none()
            if not ss:
                print("Adding missing Security Settings to Admin...")
                admin_user.security_settings = SecuritySettings()
                session.add(admin_user)
                await session.flush()

        # 2. Categories
        cat_perfume = Category(name="Perfumes", slug="perfumes")
        cat_electronics = Category(name="Electronics", slug="electronics")
        session.add_all([cat_perfume, cat_electronics])
        await session.flush()

        # 3. Products & Variants
        # Product 1
        # 3. Products & Variants
        # Product 1
        # Re-defining P1 correctly
        p1 = Product(
            name="Luxurious Oud",
            description="Premium Arabian Oud",
            category_id=cat_perfume.id,
            product_type=ProductType.PHYSICAL,
            slug="luxurious-oud"
        )
        session.add(p1)
        await session.flush()
        
        v1 = ProductVariant(
            product_id=p1.id,
            sku="sk_oud_001",
            price=250.0,
            cost_price=100.0,
            options=json.dumps({"size": "100ml"})
        )
        session.add(v1)
        await session.flush()
        
        # Stock for V1
        inv1 = InventoryItem(variant_id=v1.id, warehouse_id=wh.id, quantity=50)
        session.add(inv1)

        # Product 2
        p2 = Product(
            name="iPhone 15 Pro",
            description="Titanium Blue",
            category_id=cat_electronics.id,
            product_type=ProductType.PHYSICAL,
            slug="iphone-15-pro"
        )
        session.add(p2)
        await session.flush()
        
        v2 = ProductVariant(
            product_id=p2.id,
            sku="sk_iphone_15",
            price=4500.0,
            cost_price=4000.0,
            options=json.dumps({"color": "Blue", "storage": "256GB"})
        )
        session.add(v2)
        await session.flush()
        
        # Stock for V2
        inv2 = InventoryItem(variant_id=v2.id, warehouse_id=wh.id, quantity=10)
        session.add(inv2)

        # Customers
        c1 = Customer(name="Walk-in Customer", email="walkin@store.com")
        c2 = Customer(name="VIP Client", email="vip@store.com")
        session.add_all([c1, c2])

        await session.commit()
        print("Demo Data Seeded Successfully!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_demo_data())
