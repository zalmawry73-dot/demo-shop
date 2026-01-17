
import json
# import httpx - Not available in env
import asyncio
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import PaymentConfig, Order

class PaymentGateway(ABC):
    @abstractmethod
    async def process_payment(self, amount: float, currency: str, payment_details: dict) -> dict:
        pass

class DummyGateway(PaymentGateway):
    async def process_payment(self, amount: float, currency: str, payment_details: dict) -> dict:
        # Simulate success
        return {"status": "success", "transaction_id": "dummy_txn_12345"}

class StripeGateway(PaymentGateway):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stripe.com/v1"

    async def process_payment(self, amount: float, currency: str, payment_details: dict) -> dict:
        if not self.api_key:
             return {"status": "failed", "error": "Missing Stripe API Key"}

        # Use token or payment_method_id from details
        token = payment_details.get("token")
        
        # Simple Charge (Legacy) or PaymentIntent
        try:
            # Mock Async HTTP Call
            await asyncio.sleep(0.5) 
            # In real implementation use aiohttp or similar
            if amount < 0: raise Exception("Invalid Amount")
        except Exception as e:
            return {"status": "failed", "error": str(e)}

        return {"status": "success", "transaction_id": f"stripe_chk_{amount}"}

class PaymentService:
    @staticmethod
    async def process_order_payment(db: AsyncSession, order: Order, provider_name: str, payment_details: dict) -> dict:
        # 1. Fetch Config
        stmt = select(PaymentConfig).where(PaymentConfig.provider_name == provider_name)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config or not config.is_active:
             return {"status": "failed", "error": f"Provider {provider_name} not available"}

        # 2. Select Gateway
        gateway = None
        if provider_name == 'stripe':
            api_key = config.config.get("api_key")
            gateway = StripeGateway(api_key)
        elif provider_name == 'cod':
            gateway = DummyGateway()
        else:
            return {"status": "failed", "error": "Unknown Provider implementation"}

        # 3. Process
        try:
            # Multi-currency support placeholder
            currency = "SAR" 
            result = await gateway.process_payment(order.total_amount, currency, payment_details)
            
            if result.get("status") == "success":
                order.payment_status = "paid"
                order.payment_method = provider_name
                # store txn id if column existed, or in json
            
            return result
        except Exception as e:
            return {"status": "failed", "error": str(e)}
