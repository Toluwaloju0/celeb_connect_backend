""" a module to create the celebrity model for login and database saving """

import enum

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel
from typing import List

from .base_model import Base, Basemodel
from .avalilability_model import Availability

class CelebCreate(BaseModel):
    """ The class to create a new celebrity class """

    name: str
    location: str
    marital_status: str
    profession: str


class Celeb(Basemodel, Base):
    """The orm for the celeb_class in the database"""

    __tablename__ = "celebs"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str] = mapped_column(String(256), nullable=True)
    profession: Mapped[str] = mapped_column(String(60), nullable=False)
    marital_status: Mapped[str] = mapped_column(String(60), nullable=True)
    profile_url: Mapped[str] = mapped_column(String(60), nullable=True, default=None)
    bio: Mapped[str] = mapped_column(String(1024), nullable=True)
    
    agent_id: Mapped[str] = mapped_column(String(60), ForeignKey("agents.id"))

    agent: Mapped["Agent"] = relationship(back_populates="celebs")
    availability: Mapped["Availability"] = relationship(back_populates="celeb", cascade="all, delete, delete-orphan")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="celeb", cascade="all, delete, delete-orphan")

    def __init__(self, name: str, location: str, profession: str, marital_status: str | None = None):
        """ the class initializer
        Args:
            name(str): the celeb name
            location (str): the celeb location
            profession(str): the celeb profession
            marital_status: the celelb marital status
        """

        self.name = name
        self.location = location
        self.profession = profession
        self.marital_status = marital_status
        self.profile_url = None
        self.bio = None

        super().__init__()

        self.availability = Availability()
