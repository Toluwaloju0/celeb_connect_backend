""" a module to set the availability model for the agents """

import enum

from sqlalchemy import String, ForeignKey, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from pydantic import BaseModel

from .base_model import Base, Basemodel

class Type(str, enum.Enum):
    """The type of the booking """

    ONE_TIME = "One-Time"
    VACATION = "Vacation"
    LONG_MEET = "Long-Meet"

class Weekday(str, enum.Enum):
    """ a class to show the accepted weekdays """

    Mo = "MONDAY"
    Tu = "TUESDAY"
    We = "WEDNESSDAY"
    Th = "THURSDAY"
    Fr = "FRIDAY"

class UserWeekDay(BaseModel):
    """ a class to show the accepted weekdays """

    day: Weekday
    type: Type

class AgentWeekDay(BaseModel):
    """ a class to show define a list of days which an admin approves for a celeb """

    days: List[Weekday]


class Availability(Basemodel, Base):
    """ the availability class """

    __tablename__ = "availability"

    celeb_id: Mapped[str] = mapped_column(String(60), ForeignKey("celebs.id"))
    monday: Mapped[bool] = mapped_column(Boolean, default=True)
    tuesday: Mapped[bool] = mapped_column(Boolean, default=True)
    wednessday: Mapped[bool] = mapped_column(Boolean, default=True)
    thursday: Mapped[bool] = mapped_column(Boolean, default=True)
    friday: Mapped[bool] = mapped_column(Boolean, default=True)
    
    celeb: Mapped["Celeb"] = relationship(back_populates="availability")
