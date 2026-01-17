import asyncio
import sys
import os
from datetime import datetime

# Add current path
sys.path.append(os.getcwd())

from models import Base, Order, Customer, OrderStatus, Analytics, User
from database import engine, AsyncSessionLocal
from sqlalchemy import select

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if data exists
        result = await session.execute(select(Order))
        if result.scalars().first():
            print("Data already exists.")
            return

        print("Seeding data...")
        
        # Create Customer
        cust = Customer(name="Test Customer", email="test@test.com")
        session.add(cust)
        await session.flush()

        # Create Analytics
        analytics = Analytics(date=datetime.now(), visits=100)
        session.add(analytics)

        # Create Orders
        # 1. Completed Order
        o1 = Order(
            customer_id=cust.id, 
            status=OrderStatus.COMPLETED, 
            payment_status="paid", 
            payment_method="card",
            total_amount=500.0,
            is_draft=False
        )
        
        # 2. New Order
        o2 = Order(
            customer_id=cust.id, 
            status=OrderStatus.NEW, 
            payment_status="unpaid", 
            payment_method="cod",
            total_amount=150.0,
            is_draft=False
        )

        session.add_all([o1, o2])
        await session.commit()
        print("Data seeded successfully!")

async def test_endpoints():
    # We will import app and use httpx (async requests) to test it, 
    # but to avoid installing httpx just for this, 
    # we can call the service functions directly or simulation.
    # However, running the server is better.
    # For now, let's just run the DB queries using the same logic as the endpoints to verify ORM.
    
    async with AsyncSessionLocal() as session:
        print("\n--- Testing Stats Logic ---")
        # Sales
        from sqlalchemy import func
        sales = await session.execute(select(func.sum(Order.total_amount)).where(Order.status == OrderStatus.COMPLETED))
        print(f"Total Sales (Expected 500.0): {sales.scalar()}")
        
        # Recent Orders
        print("\n--- Testing Recent Orders Logic ---")
        from sqlalchemy.orm import selectinload
        stmt = select(Order).options(selectinload(Order.customer)).order_by(Order.created_at.desc()).limit(5)
        res = await session.execute(stmt)
        orders = res.scalars().all()
        for o in orders:
            print(f"Order #{o.id} - {o.customer.name} - {o.total_amount}")

if __name__ == "__main__":
    # Initialize DB tables first
    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        await seed_data()
        await test_endpoints()

    asyncio.run(init())
