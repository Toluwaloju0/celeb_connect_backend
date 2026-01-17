""" a module to create the function to save otp code"""

from sqlalchemy import String, Integer
from sqlalchemy.orm import mapped_column, Mapped
from pydantic import BaseModel, Field

from .base_model import Basemodel, Base


class OTPRequest(BaseModel):
    otp_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-character OTP code"
    )
    

class OtpCode(Basemodel, Base):
    """ the otp code class """
    
    __tablename__ = "otp_codes"

    code: Mapped[str] = mapped_column(String(10), nullable=False)
    email: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    count: Mapped[int] = mapped_column(Integer, default=0)

    def __init__(self, email: str, code: str):
        """ the class initializer
        Args:
            email: the email address the otp code is been sent to
            code: the code which is been sent
        """

        super().__init__()
        self.code = code
        self.email = email
        self.count = 0
