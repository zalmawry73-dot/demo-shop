from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.modules.marketing.models import Coupon
from pydantic import BaseModel

router = APIRouter(prefix="/api/marketing", tags=["Marketing"])

class CouponResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    value: float

    class Config:
        orm_mode = True

@router.get("/coupons", response_model=List[CouponResponse])
async def list_coupons(db: AsyncSession = Depends(get_db)):
    """List all coupons for selection in settings."""
    stmt = select(Coupon).where(Coupon.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()
