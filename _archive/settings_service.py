
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import StoreSettings, ShippingRule, ShippingConditionType

class ConfigurationService:
    @staticmethod
    async def get_settings(db: AsyncSession) -> StoreSettings:
        # Singleton pattern for settings
        stmt = select(StoreSettings).limit(1)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()
        
        if not settings:
            # Create default if missing
            settings = StoreSettings()
            db.add(settings)
            await db.commit()
            await db.refresh(settings)
            
        return settings

    @staticmethod
    def calculate_tax(amount: float, settings: StoreSettings) -> dict:
        """
        Returns tax details based on policy.
        """
        rate = settings.tax_rate
        
        if settings.tax_inclusive:
            # Price = Base + Tax
            # Base = Price / (1 + Rate)
            base_amount = amount / (1 + rate)
            tax_amount = amount - base_amount
        else:
            # Price = Base
            # Tax = Base * Rate
            base_amount = amount
            tax_amount = amount * rate
            
        return {
            "taxable_amount": round(base_amount, 2),
            "tax_amount": round(tax_amount, 2),
            "rate": rate
        }

    @staticmethod
    async def calculate_shipping(db: AsyncSession, cart_total: float, total_weight: float = 0.0, zone: str = "All") -> float:
        """
        Finds the best matching shipping rule.
        Priority: Matches Zone -> Cheapest Valid Rule.
        """
        # Fetch active rules for the zone or 'All'
        stmt = select(ShippingRule).where(
            ShippingRule.is_active == True,
            (ShippingRule.zone == zone) | (ShippingRule.zone == "All")
        )
        result = await db.execute(stmt)
        rules = result.scalars().all()
        
        applicable_costs = []
        
        for rule in rules:
            if rule.condition_type == ShippingConditionType.FIXED:
                applicable_costs.append(rule.cost)
            
            elif rule.condition_type == ShippingConditionType.PRICE_BASED:
                if cart_total >= rule.condition_value:
                    applicable_costs.append(rule.cost)
                    
            elif rule.condition_type == ShippingConditionType.WEIGHT_BASED:
                if total_weight >= rule.condition_value:
                    applicable_costs.append(rule.cost)
        
        if not applicable_costs:
            return 50.0 # Default fallback cost if no rules match
            
        return min(applicable_costs) # Return the best rate for the customer
