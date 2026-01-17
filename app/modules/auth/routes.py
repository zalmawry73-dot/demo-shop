
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.schemas import Token
from app.modules.auth.models import User
from app.modules.auth.schemas import UserUpdate, PasswordChange, UserRead
from app.modules.auth.service import update_user_profile, change_password
from app.dependencies import get_current_user
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter(tags=["Auth"])

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    # Find user
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "token_version": user.token_version}, 
        expires_delta=access_token_expires
    )
    
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

from fastapi import Request
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/account/settings")
async def account_settings_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse("account_settings.html", {"request": request, "user": current_user})

@router.put("/account/profile", response_model=UserRead)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await update_user_profile(db, current_user, update_data)

@router.post("/account/password")
async def update_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await change_password(db, current_user, password_data)

# Security Settings Endpoints
from app.modules.auth.schemas import SecuritySettingsRead, SecuritySettingsUpdate
from app.modules.auth.models import SecuritySettings

@router.get("/account/security", response_model=None) # Returns HTML
async def account_security_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Ensure security settings exist (lazy load check)
    if not current_user.security_settings:
        # Create if missing (sanity check)
        ss = SecuritySettings(user_id=current_user.id)
        db.add(ss)
        await db.commit()
        await db.refresh(current_user)
        
    return templates.TemplateResponse("security_settings.html", {
        "request": request, 
        "user": current_user,
        "settings": current_user.security_settings
    })

@router.put("/api/account/security", response_model=SecuritySettingsRead)
async def update_security_settings(
    settings_data: SecuritySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.security_settings:
         # Should exist by now, but handle safely
         ss = SecuritySettings(user_id=current_user.id)
         db.add(ss)
         await db.commit()
         await db.refresh(current_user)

    # Update logic
    ss = current_user.security_settings
    
    # Manually update fields
    ss.two_factor_enabled = settings_data.two_factor_enabled
    ss.export_password_protection = settings_data.export_password_protection
    ss.otp_method = settings_data.otp_method
    ss.session_policy = settings_data.session_policy
    
    await db.commit()
    await db.refresh(ss)
    return ss

@router.post("/api/account/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Increment token version
    current_user.token_version += 1
    await db.commit()
    return {"message": "Logged out from all other devices"}
