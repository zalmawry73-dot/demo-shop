from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class OrderItemSchema(BaseModel):
    variant_id: int
    quantity: int

class OrderCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[OrderItemSchema]
    discount_detail: Optional[Dict[str, Any]] = {}
    # payment_details: Optional[Dict[str, float]] = None # For POS split payment

class OrderResponse(BaseModel):
    id: int
    status: str
    total_amount: float

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
