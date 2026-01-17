
import asyncio
from database import AsyncSessionLocal
from models import Product, ProductVariant, ShippingRule, ShippingConditionType, StoreSettings, User, Order, OrderStatus
from settings_service import ConfigurationService
from schemas import OrderCreate, OrderItemSchema 
# Note: We need to use schema for input

async def verify_checkout_flow():
    async with AsyncSessionLocal() as session:
        print("--- Cleaning DB ---")
        from sqlalchemy import text
        # Clean specific tables to avoid unique errors
        await session.execute(text("DELETE FROM order_items"))
        await session.execute(text("DELETE FROM orders"))
        await session.execute(text("DELETE FROM stock_movements"))
        await session.execute(text("DELETE FROM inventory_items"))
        await session.execute(text("DELETE FROM product_variants"))
        await session.execute(text("DELETE FROM products"))
        await session.execute(text("DELETE FROM shipping_rules"))
        await session.execute(text("DELETE FROM store_settings"))
        await session.execute(text("DELETE FROM payment_configs"))
        await session.commit()

        print("--- Setup Test Data ---")
        
        # 1. Product with Weight
        p = Product(name="Heavy Widget", description="Desc", product_type="physical", weight=5.0) # 5kg
        session.add(p)
        await session.commit()
        await session.refresh(p)
        
        v = ProductVariant(product_id=p.id, sku="HW-001", price=100.0, cost_price=50.0, attributes={})
        session.add(v)
        await session.commit()
        await session.refresh(v)
        
        # 2. Shipping Rule (Weight > 8kg = 50 SAR)
        rule = ShippingRule(name="Heavy Shipping", zone="All", condition_type=ShippingConditionType.WEIGHT_BASED, condition_value=8.0, cost=50.0, is_active=True)
        session.add(rule)
        
        # 3. Settings (Tax 15% Exclusive)
        settings = await ConfigurationService.get_settings(session)
        settings.tax_inclusive = False
        settings.tax_rate = 0.15
        
        await session.commit()
        
        # 4. Create Order Payload (2 Items = 10kg Total => Should Trigger Shipping)
        # We can't easily call the API function directly because of Dependencies.
        # But we can simulate the logic flow or use httpx to hit running server? 
        # Using Direct Logic simulation is safer/faster for unit testing logic blocks, 
        # but let's try to verify via script logic that mirrors main.py or just trust previous unit tests?
        # Let's write a targeted test that calls the Service/Entity logic directly if possible, 
        # but `create_order` is big. 
        # Best approach: Use TestClient? No, `main` not imported easily.
        # We will replicate the KEY logic block here to verify integration.
        
        print("\n--- Simulating Checkout Logic ---")
        cart_qty = 2
        total_weight = p.weight * cart_qty # 10.0
        subtotal = v.price * cart_qty # 200.0
        
        print(f"Cart: {cart_qty}x {p.name} (Weight: {total_weight}kg, Subtotal: {subtotal})")
        
        # Calcs
        ship_cost = await ConfigurationService.calculate_shipping(session, subtotal, total_weight, "All")
        print(f"Shipping Cost: {ship_cost}")
        assert ship_cost == 50.0 # From Rule
        
        taxable = subtotal + ship_cost # 250
        tax = ConfigurationService.calculate_tax(taxable, settings)
        print(f"Tax: {tax}")
        assert tax['tax_amount'] == 37.5 # 15% of 250
        
        total = taxable + tax['tax_amount']
        print(f"Total: {total}")
        assert total == 287.5
        
        print("\n--- Payment Service Test ---")
        from payment_service import PaymentService
        # Setup Payment Config (Mock)
        from models import PaymentConfig
        pc = PaymentConfig(provider_name='stripe', display_name='Stripe', is_active=True, config={"api_key": "sk_test_123"})
        session.add(pc)
        await session.commit()
        
        dummy_order = Order(total_amount=total, payment_status="pending")
        res = await PaymentService.process_order_payment(session, dummy_order, "stripe", {"token": "tok_123"})
        print(f"Payment Result: {res}")
        assert res['status'] == "success"

if __name__ == "__main__":
    asyncio.run(verify_checkout_flow())
