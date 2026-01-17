
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db

from app.core.security import SECRET_KEY, ALGORITHM
from app.core.schemas import TokenData
from app.modules.auth.models import User

from fastapi import Request

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_token_from_cookie_or_header(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if token:
        # Remove Bearer prefix if present (though cookie usually just has the token)
        if token.startswith("Bearer "):
            return token.split(" ")[1]
        return token
    
    # Fallback to Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    return None

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    token = await get_token_from_cookie_or_header(request)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        # Check if it's an API call or HTML request to decide response? 
        # For now, just raise 401. UI will redirect to login.
        raise credentials_exception

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    stmt = select(User).options(selectinload(User.security_settings)).where(User.username == token_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    # Security: Check Token Version
    token_version = payload.get("token_version")
    if token_version is not None and token_version != user.token_version:
        raise credentials_exception
        
    return user
