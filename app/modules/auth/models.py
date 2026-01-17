
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Boolean, Enum, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, Enum, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.models import TimeStampedModel

class WorkGroup(TimeStampedModel):
    __tablename__ = "work_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    permissions: Mapped[dict] = mapped_column(JSON, default={})
    
    users: Mapped[list["User"]] = relationship("User", back_populates="group")

class UserRole(str, PyEnum):
    ADMIN = "admin"
    MERCHANT = "merchant"
    STAFF = "staff"

class Gender(str, PyEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class User(TimeStampedModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STAFF)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    group_id: Mapped[int] = mapped_column(ForeignKey("work_groups.id"), nullable=True)
    group: Mapped["WorkGroup"] = relationship("WorkGroup", back_populates="users")

    # Profile Fields
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=True)
    
    # Security
    token_version: Mapped[int] = mapped_column(Integer, default=1)
    
    security_settings: Mapped["SecuritySettings"] = relationship("SecuritySettings", back_populates="user", uselist=False, cascade="all, delete-orphan")


class SessionPolicy(str, PyEnum):
    NORMAL = "normal"   # 24 hours
    MEDIUM = "medium"   # 2 hours
    HIGH = "high"       # 30 mins

class OTPMethod(str, PyEnum):
    SMS = "sms"
    EMAIL = "email"

class SecuritySettings(TimeStampedModel):
    __tablename__ = "security_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    export_password_protection: Mapped[bool] = mapped_column(Boolean, default=False)
    otp_method: Mapped[OTPMethod] = mapped_column(Enum(OTPMethod), default=OTPMethod.SMS)
    session_policy: Mapped[SessionPolicy] = mapped_column(Enum(SessionPolicy), default=SessionPolicy.NORMAL)

    user: Mapped["User"] = relationship("User", back_populates="security_settings")

class Analytics(TimeStampedModel):
    __tablename__ = "analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True)
    visits: Mapped[int] = mapped_column(Integer, default=0)
