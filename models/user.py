"""The user model to be used """

import enum

from datetime import date, datetime
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr
from typing import List

from .base_model import Base, Basemodel

class UserCreate(BaseModel):
    """ a classs to use as the request body object for my API"""

    first_name: str
    last_name: str
    email: EmailStr
    date_of_birth: datetime
    password: str
    phone_number: str


class UserLogin(BaseModel):
    """ a class for all login processes"""
    email: EmailStr
    password: str

class UserLevel(str, enum.Enum):
    """ the enum class for the user levels """

    UNVERIFIED = "Unverified"
    VERIFIED = "Verified"
    BASIC = "Basic"
    PREMIUM = "Premium"

class UpdateUserLevel(BaseModel):
    """ a class to get a tier used to update a user level"""

    new_level: UserLevel

class User(Basemodel, Base):

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    date_of_birth: Mapped[datetime] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(String(2048), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(60), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    level: Mapped[UserLevel] = mapped_column(Enum(UserLevel), default=UserLevel.UNVERIFIED)
    old_level: Mapped[UserLevel] = mapped_column(Enum(UserLevel), default=UserLevel.UNVERIFIED)

    bookings: Mapped[List["Booking"]] = relationship(back_populates="user", cascade="all, delete, delete-orphan")
    refresh_token: Mapped["RefreshToken"] = relationship(back_populates="user", cascade="all, delete, delete-orphan")

    def __init__(
        self, 
        first_name: str,
        last_name: str,
        email: str,
        date_of_birth: date,
        password: str,
        phone_number: str
    ):
        
        super().__init__()

        self.name = f"{first_name} {last_name}"
        self.email = email
        self.password = password
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.is_verified = False
        self.level = UserLevel.UNVERIFIED
        self.old_level = UserLevel.UNVERIFIED
