"""a module to create a booking model class """

import enum

from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel

from .base_model import Base, Basemodel
from .avalilability_model import Weekday

class Status(str, enum.Enum):
    """ a  class to show the status of a booking"""

    APPROVED = "Approved"
    PENDING = "Pending"
    CANCELLED = "Cancelled"
    PAID = "Paid"

class Type(str, enum.Enum):
    """The type of the booking """

    ONE_TIME = "One-Time"
    VACATION = "Vacation"
    LONG_MEET = "Long-Meet"

class BookingStatus(BaseModel):
    status: Status

class Booking(Basemodel, Base):
    """ the bookings class """

    __tablename__ = "bookings"

    celeb_id: Mapped[str] = mapped_column(String(60), ForeignKey("celebs.id"))
    user_id: Mapped[str] = mapped_column(String(60), ForeignKey("users.id"))
    day: Mapped[Weekday] = mapped_column(Enum(Weekday), nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.PENDING)
    type: Mapped[Type] = mapped_column(Enum(Type), nullable=False)

    celeb: Mapped["Celeb"] = relationship(back_populates="bookings")
    user: Mapped["User"] = relationship(back_populates="bookings")

    def __init__(self, day: Weekday, user_id, type: Type):
        """ the class initializer """

        self.day = day
        self.user_id = user_id
        self.type = type

        super().__init__()