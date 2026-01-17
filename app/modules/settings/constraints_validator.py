"""
Constraints Validation Service
Validates shipping and payment constraints before order creation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.modules.settings.models import ShippingConstraint, PaymentConstraint
from typing import List, Dict, Any


class ConstraintsValidator:
    
    @staticmethod
    async def validate_shipping_constraints(
        db: AsyncSession,
        shipping_company_id: str,
        cart_total: float,
        product_ids: List[int],
        customer_location: str = None
    ) -> Dict[str, Any]:
        """
        Validate if shipping company is allowed based on active constraints
        Returns: {"allowed": bool, "error_message": str}
        """
        # Get all active shipping constraints
        stmt = select(ShippingConstraint).where(
            ShippingConstraint.is_active == True
        ).options(selectinload(ShippingConstraint.conditions))
        
        result = await db.execute(stmt)
        constraints = result.scalars().all()
        
        for constraint in constraints:
            # Check if this constraint applies to the selected shipping company
            if shipping_company_id in constraint.shipping_company_ids:
                # Check all conditions
                constraint_violated = False
                
                for condition in constraint.conditions:
                    if condition.type == "CART_TOTAL":
                        operator = condition.operator
                        value = condition.value
                        
                        if operator == "GT" and cart_total <= value.get("amount", 0):
                            constraint_violated = True
                        elif operator == "LT" and cart_total >= value.get("amount", 0):
                            constraint_violated = True
                        elif operator == "BETWEEN":
                            min_val = value.get("min", 0)
                            max_val = value.get("max", 999999)
                            if not (min_val <= cart_total <= max_val):
                                constraint_violated = True
                    
                    elif condition.type == "PRODUCT":
                        # Check if any restricted product is in cart
                        restricted_products = condition.value.get("product_ids", [])
                        if any(pid in restricted_products for pid in product_ids):
                            constraint_violated = True
                    
                    elif condition.type == "LOCATION":
                        # Check if customer location matches restriction
                        restricted_locations = condition.value.get("locations", [])
                        if customer_location and customer_location in restricted_locations:
                            constraint_violated = True
                
                # If constraint is violated, shipping is blocked
                if constraint_violated:
                    error_message = constraint.custom_error_message if constraint.is_custom_error_enabled else \
                                   f"شركة الشحن المحددة غير متاحة لهذا الطلب"
                    return {
                        "allowed": False,
                        "error_message": error_message
                    }
        
        return {"allowed": True, "error_message": None}
    
    @staticmethod
    async def validate_payment_constraints(
        db: AsyncSession,
        payment_method_id: str,
        cart_total: float,
        product_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Validate if payment method is allowed based on active constraints
        Returns: {"allowed": bool, "error_message": str}
        """
        # Get all active payment constraints
        stmt = select(PaymentConstraint).where(
            PaymentConstraint.is_active == True
        ).options(selectinload(PaymentConstraint.conditions))
        
        result = await db.execute(stmt)
        constraints = result.scalars().all()
        
        for constraint in constraints:
            # Check if this constraint applies to the selected payment method
            if payment_method_id in constraint.payment_method_ids:
                constraint_violated = False
                
                for condition in constraint.conditions:
                    if condition.type == "CART_TOTAL":
                        operator = condition.operator
                        value = condition.value
                        
                        if operator == "GT" and cart_total <= value.get("amount", 0):
                            constraint_violated = True
                        elif operator == "LT" and cart_total >= value.get("amount", 0):
                            constraint_violated = True
                        elif operator == "BETWEEN":
                            min_val = value.get("min", 0)
                            max_val = value.get("max", 999999)
                            if not (min_val <= cart_total <= max_val):
                                constraint_violated = True
                    
                    elif condition.type == "PRODUCT":
                        restricted_products = condition.value.get("product_ids", [])
                        if any(pid in restricted_products for pid in product_ids):
                            constraint_violated = True
                
                if constraint_violated:
                    error_message = constraint.custom_error_message if constraint.is_custom_error_enabled else \
                                   f"طريقة الدفع المحددة غير متاحة لهذا الطلب"
                    return {
                        "allowed": False,
                        "error_message": error_message
                    }
        
        return {"allowed": True, "error_message": None}
