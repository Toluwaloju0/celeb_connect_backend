""" a module to define the agent model """

import enum

from sqlalchemy import String, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr
from typing import List

from .base_model import Base, Basemodel

class AgentCreate(BaseModel):
    """ The class to use in creating a new agent"""

    name: str
    email: EmailStr
    phone_number: str

class AgentLogin(BaseModel):
    """ the class for logging in agents to the applicaton """
    
    email: EmailStr
    password: str

class AgentTier(int, enum.Enum):
    """The agents level"""

    JUNIOR = 1
    CERTIFIED = 2
    SENIOR = 3
    MANAGER = 4
    OWNER = 5

class Agent(Basemodel, Base):
    """ the agent class """

    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String(60), nullable=True)
    tier: Mapped[AgentTier] = mapped_column(Enum(AgentTier), default=AgentTier.JUNIOR, nullable=False)
    admin_id: Mapped[str] = mapped_column(String(60), ForeignKey("admin.id"))
    password: Mapped[str] = mapped_column(String(2048), nullable=False)
    number_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    admin: Mapped["Admin"] = relationship(back_populates="agents")
    refresh_token: Mapped["AgentRefresh"] = relationship(back_populates="agent", cascade="all, delete")
    celebs: Mapped[List["Celeb"]] = relationship(back_populates="agent", cascade="all, delete")

    def __init__(self, name, email, password, phone_number = None):
        """ the class initializer
        Args:
            name: the name of the agent
            email: the email address of the agent
            phone_number: the phone number of the agent
        """

        self.name = name
        self.email = email
        self.phone_number = phone_number
        self.tier = AgentTier.JUNIOR
        self.password = password
        super().__init__()
