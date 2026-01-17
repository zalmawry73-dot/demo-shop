from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr
from app.modules.auth.models import Gender, UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    role: UserRole = UserRole.STAFF
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    email: Optional[EmailStr] = None

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

from app.modules.auth.models import SessionPolicy, OTPMethod

class SecuritySettingsBase(BaseModel):
    two_factor_enabled: bool = False
    export_password_protection: bool = False
    otp_method: OTPMethod = OTPMethod.SMS
    session_policy: SessionPolicy = SessionPolicy.NORMAL

class SecuritySettingsUpdate(SecuritySettingsBase):
    pass

class SecuritySettingsRead(SecuritySettingsBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True
