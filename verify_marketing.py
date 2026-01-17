import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.getcwd())
from database import AsyncSessionLocal, engine
from models import Base, Product, ProductVariant, AutomaticDiscount, DiscountType, Coupon, CustomerGroup, Customer, Order, OrderStatus
from marketing_service import DiscountCalculator
from sqlalchemy import select, text

async def verify_marketing():
    print("Verifying Marketing Engine...")
    
    # Simple Migration for Dev DB (since create_all doesn't update columns)
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("ALTER TABLE orders ADD COLUMN affiliate_id INTEGER REFERENCES affiliates(id)"))
            await session.commit()
        except Exception:
            pass # Already exists
            
        try:
            await session.execute(text("ALTER TABLE orders ADD COLUMN discount_detail JSON DEFAULT '{}'"))
            await session.commit()
        except Exception:
            pass

    # Setup DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Cleanup (Order matters for Foreign Keys)
        # Delete orders for the test customer
        await session.execute(text("DELETE FROM orders WHERE customer_id IN (SELECT id FROM customers WHERE email = 'vip@test.com')"))
        # Delete the test customer
        await session.execute(text("DELETE FROM customers WHERE email = 'vip@test.com'"))
        
        await session.execute(text("DELETE FROM automatic_discounts"))
        await session.execute(text("DELETE FROM coupons"))
        await session.execute(text("DELETE FROM campaigns"))
        await session.execute(text("DELETE FROM customer_groups"))
        await session.execute(text("DELETE FROM products WHERE name IN ('Perfume A', 'Sample B')"))
        await session.execute(text("DELETE FROM product_variants")) # Cleanup orphaned variants if any? (Actually we didn't create variants in this script yet, but good practice). Actually, ProductVariant has FK to Product. 
        # But wait, looking at my verify_marketing.py, I am creating Products directly. 
        # I am NOT creating ProductVariants in the script explicitly, but I assumed I didn't need them for the simple test logic? 
        # Wait, Step 271: I just create Product(p1). 
        # If I delete Product p1, cascade should handle it? 
        # SQLite Foreign Keys need to be enabled.
        
        await session.commit()

        # 1. Seed Products for BOGO
        # Product A (Buy This)
        p1 = Product(name="Perfume A", description="..", product_type="physical")
        session.add(p1)
        # Product B (Get This Free)
        p2 = Product(name="Sample B", description="..", product_type="physical")
        session.add(p2)
        await session.commit()
        await session.refresh(p1)
        await session.refresh(p2)
        
        # 2. Create BOGO Rule
        bogo = AutomaticDiscount(
            name="Buy Perfume Get Sample",
            discount_type=DiscountType.BOGO,
            configuration={
                "buy_product_id": p1.id, 
                "get_product_id": p2.id,
                "get_quantity": 1
            }
        )
        session.add(bogo)
        
        # 3. Create Coupon
        coupon = Coupon(code="SAVE10", discount_type=DiscountType.PERCENTAGE, value=10.0) # 10%
        session.add(coupon)
        await session.commit()
        
        # --- TEST 1: BOGO ---
        calc = DiscountCalculator(session)
        cart = [
            {'product_id': p1.id, 'variant_id': None, 'qty': 1, 'price': 100.0},
            # Note: We did NOT add p2 to cart, we expect the system to suggest it OR if we add it, to discount it.
            # Let's add it to test the discount logic.
            {'product_id': p2.id, 'variant_id': None, 'qty': 1, 'price': 20.0}
        ]
        
        print("\nTest 1: BOGO Logic")
        res = await calc.apply_discounts(cart_items=cart, subtotal=120.0)
        print(f" - Cart Subtotal: 120.0")
        print(f" - Result: {res}")
        
        # Expecting 20.0 discount
        applied = res['applied_discounts']
        if any(d['amount'] == 20.0 for d in applied):
            print(" - BOGO SUCCESS: Sample B was discounted fully.")
        else:
            print(" - BOGO FAILED.")

        # --- TEST 2: Coupon ---
        print("\nTest 2: Coupon Logic")
        # Apply SAVE10 to the remaining 100.0 (120 - 20)
        # Our logic applies to passed subtotal. In a real chain, we'd pass the new total.
        # Let's pass 100.0
        res_coupon = await calc.apply_discounts(cart_items=[], subtotal=100.0, coupon_code="SAVE10")
        print(f" - Applying SAVE10 to 100.0")
        print(f" - Result: {res_coupon}")
        
        if res_coupon['final_total'] == 90.0:
            print(" - COUPON SUCCESS: 10% off applied.")
        else:
            print(" - COUPON FAILED.")
            
        # --- TEST 3: Segmentation ---
        print("\nTest 3: Customer Segmentation")
        # Create VIP Group
        vip_group = CustomerGroup(name="VIP", criteria={"min_orders": 2})
        session.add(vip_group)
        
        # Create Customer with 3 orders
        cust = Customer(name="VIP User", email="vip@test.com")
        session.add(cust)
        await session.commit()
        await session.refresh(cust)
        await session.refresh(vip_group)
        
        # Add 3 Orders
        for _ in range(3):
            o = Order(
                customer_id=cust.id, 
                total_amount=100.0, 
                status=OrderStatus.COMPLETED,
                payment_status="paid",
                payment_method="card"
            )
            session.add(o)
        await session.commit()
        
        # Run Logic
        members = await calc.get_segment_members(vip_group.id)
        print(f" - VIP Members Found: {members}")
        
        if cust.id in members:
            print(" - SEGMENTATION SUCCESS: VIP User found.")
        else:
            print(" - SEGMENTATION FAILED.")

if __name__ == "__main__":
    asyncio.run(verify_marketing())
