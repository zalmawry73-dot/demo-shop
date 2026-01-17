from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.modules.auth.models import User
from app.modules.auth.schemas import UserUpdate, PasswordChange
from app.core.security import get_password_hash, verify_password

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_profile(db: AsyncSession, user: User, update_data: UserUpdate) -> User:
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user

async def change_password(db: AsyncSession, user: User, password_data: PasswordChange):
    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الحالية غير صحيحة"
        )
    
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور الجديدة غير متطابقة"
        )
        
    user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    return {"message": "تم تغيير كلمة المرور بنجاح"}
