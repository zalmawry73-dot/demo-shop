from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class OrderItemSchema(BaseModel):
    variant_id: str  # UUID string
    quantity: int

class OrderCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[OrderItemSchema]
    payment_method: Optional[str] = "multi"  # Can be string like "cod", "transfer", or int for payment method ID
    shipping_method: Optional[str] = "standard"
    shipping_company: Optional[int] = None  # Optional shipping company ID
    discount_detail: Optional[Dict[str, Any]] = {}
    payment_details: Optional[Dict[str, float]] = {}

class OrderResponse(BaseModel):
    id: int
    status: str
    total_amount: float

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
