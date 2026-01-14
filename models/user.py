"""The user model to be used """

from datetime import date
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime
from datetime import datetime
from pydantic import BaseModel, EmailStr

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


class User(Basemodel, Base):

    __tablename__ = "users"
        
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    date_of_birth: Mapped[datetime] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(String(2048), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(60), nullable=True)

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
