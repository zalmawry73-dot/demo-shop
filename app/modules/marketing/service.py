
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.modules.marketing.models import Coupon, AutomaticDiscount, DiscountType, CustomerGroup, Affiliate, Campaign
from app.modules.auth.models import User
from app.modules.sales.models import Order
from datetime import datetime

class DiscountCalculator:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def apply_discounts(self, cart_items: list, subtotal: float, coupon_code: str = None, user_id: int = None):
        """
        cart_items: List of dicts {'variant_id': int, 'product_id': int, 'qty': int, 'price': float}
        Returns: { 'final_total': float, 'applied_discounts': list, 'cart_updates': list }
        """
        discounts = []
        cart_updates = [] # To add free items
        
        # 1. Automatic Discounts (BOGO)
        stmt = select(AutomaticDiscount).where(AutomaticDiscount.is_active == True)
        result = await self.db.execute(stmt)
        auto_rules = result.scalars().all()
        
        for rule in auto_rules:
            if rule.discount_type == DiscountType.BOGO:
                config = rule.configuration
                buy_id = config.get('buy_product_id')
                get_id = config.get('get_product_id')
                get_qty = config.get('get_quantity', 1)
                
                # Check if Buy product is in cart
                buy_item = next((item for item in cart_items if item['product_id'] == buy_id), None)
                if buy_item:
                    # Check if Get Item is already in cart, if so, discount it. If not, add it (Logic Sim)
                    get_item_in_cart = next((item for item in cart_items if item['product_id'] == get_id), None)
                    
                    if get_item_in_cart:
                        # Discount the cost of the 'get' item
                        discount_amount = get_item_in_cart['price'] * get_qty # Assuming free
                        discounts.append({"name": rule.name, "amount": discount_amount})
                        subtotal -= discount_amount
                    else:
                        # Propose adding it
                        cart_updates.append({"action": "add", "product_id": get_id, "qty": get_qty, "note": "Free Gift"})
        
        # 2. Coupon Code
        if coupon_code:
            stmt = select(Coupon).where(Coupon.code == coupon_code, Coupon.is_active == True)
            result = await self.db.execute(stmt)
            coupon = result.scalar_one_or_none()
            
            if coupon:
                # Validate Dates
                now = datetime.utcnow()
                if (coupon.valid_until and coupon.valid_until < now) or (coupon.min_spend and subtotal < coupon.min_spend):
                     pass # Invalid
                else:
                    discount_amount = 0
                    if coupon.discount_type == DiscountType.PERCENTAGE:
                        discount_amount = subtotal * (coupon.value / 100)
                    elif coupon.discount_type == DiscountType.FIXED_AMOUNT:
                        discount_amount = coupon.value
                    
                    discounts.append({"name": f"Coupon {coupon.code}", "amount": discount_amount})
                    subtotal -= discount_amount

        return {
            "final_total": max(0, subtotal),
            "applied_discounts": discounts,
            "cart_updates": cart_updates
        }

    async def get_segment_members(self, group_id: int):
        """
        Dynamic Customer Segmentation Engine.
        Translates JSON criteria to SQL.
        """
        stmt = select(CustomerGroup).where(CustomerGroup.id == group_id)
        result = await self.db.execute(stmt)
        group = result.scalar_one_or_none()
        
        if not group:
            return []
            
        criteria = group.criteria # { "min_orders": 5 }
        
        # 1. Fetch Key Stats per customer
        stmt_stats = (
            select(
                Order.customer_id, 
                func.count(Order.id).label("count"), 
                func.sum(Order.total_amount).label("spent")
            )
            .group_by(Order.customer_id)
        )
        result = await self.db.execute(stmt_stats)
        stats = result.all() # [(id, count, spent), ...]
        
        qualified_ids = []
        for row in stats:
            cid, count, spent = row
            match = True
            
            if "min_orders" in criteria and count < criteria["min_orders"]:
                match = False
            if "min_spent" in criteria and (spent or 0) < criteria["min_spent"]:
                match = False
                
            if match:
                qualified_ids.append(cid)
                
        return qualified_ids
