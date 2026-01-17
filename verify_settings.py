
import asyncio
from database import AsyncSessionLocal
from settings_service import ConfigurationService
from models import StoreSettings, ShippingRule, ShippingConditionType

async def verify_logic():
    async with AsyncSessionLocal() as session:
        print("--- Testing Tax Engine ---")
        
        # 1. Tax Exclusive
        s1 = StoreSettings(tax_inclusive=False, tax_rate=0.15)
        res1 = ConfigurationService.calculate_tax(100.0, s1)
        print(f"Exclusive (100 + 15%): {res1}")
        assert res1['tax_amount'] == 15.0
        assert res1['taxable_amount'] == 100.0
        
        # 2. Tax Inclusive
        s2 = StoreSettings(tax_inclusive=True, tax_rate=0.15)
        res2 = ConfigurationService.calculate_tax(115.0, s2)
        print(f"Inclusive (115 total): {res2}")
        # Base = 115 / 1.15 = 100. Tax = 15.
        assert res2['tax_amount'] == 15.0
        assert res2['taxable_amount'] == 100.0
        
        print("\n--- Testing Shipping Calculator ---")
        # Setup Rules
        # Rule 1: Riyadh Fixed 20
        r1 = ShippingRule(name="Riyadh Standard", zone="Riyadh", condition_type=ShippingConditionType.FIXED, cost=20.0, is_active=True)
        # Rule 2: All Weight > 10kg = 50
        r2 = ShippingRule(name="Heavy Items", zone="All", condition_type=ShippingConditionType.WEIGHT_BASED, condition_value=10.0, cost=50.0, is_active=True)
        
        session.add(r1)
        session.add(r2)
        await session.commit() # Note: This adds to DB, will be wiped by reset_db eventually or use test db
        
        # Test 1: Riyadh Order (Should match r1 first priority is usually zone specific if implemented, but our logic finds all matches and takes min)
        # Our Logic: Filter by Zone=Riyadh OR All. Then check conditions. Then min() cost.
        
        # Case A: Riyadh, Weight 5kg.
        # Matches: r1 (Fixed 20). r2 (Weight 5 < 10, No). 
        cost_a = await ConfigurationService.calculate_shipping(session, cart_total=100, total_weight=5, zone="Riyadh")
        print(f"Riyadh, 5kg: {cost_a} (Exp: 20)")
        
        # Case B: Riyadh, Weight 15kg.
        # Matches: r1 (20). r2 (Weight 15 > 10, Yes -> 50).
        # Min(20, 50) = 20.
        cost_b = await ConfigurationService.calculate_shipping(session, cart_total=100, total_weight=15, zone="Riyadh")
        print(f"Riyadh, 15kg: {cost_b} (Exp: 20 - Cheapest wins)")

        # Case C: Dammam, Weight 15kg.
        # Matches: r1 (Zone mismatch). r2 (Weight 15 > 10, Yes -> 50).
        cost_c = await ConfigurationService.calculate_shipping(session, cart_total=100, total_weight=15, zone="Dammam")
        print(f"Dammam, 15kg: {cost_c} (Exp: 50)")

if __name__ == "__main__":
    asyncio.run(verify_logic())
