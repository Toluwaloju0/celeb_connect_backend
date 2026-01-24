""" a module to create the admin table who manages the agents """

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr
from typing import List

from .base_model import Base, Basemodel
from utils.check_password import ph
from utils.id_string import uuid

class AdminLogin(BaseModel):
    """ the class to use when an admin wants to login to the app """

    email: EmailStr
    password: str


class Admin(Basemodel, Base):
    """ The admin class """

    __tablename__ = "admin"

    name: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[str] = mapped_column(String(60), nullable=False)
    password: Mapped[str] = mapped_column(String(1024), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(60), nullable=True)

    agents: Mapped[List["Agent"]] = relationship(back_populates="admin", cascade="all, delete")
