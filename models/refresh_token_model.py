""" a module to define the refresh token model for saving refresh tokens """

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Basemodel, Base

class RefreshToken(Basemodel, Base):
    """ the refresh token class """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(String(60), ForeignKey("users.id"), nullable=False)

    def __init__(self, user_id):
        """ the initializer for the refresh token object"""

        super().__init__()

        self.user_id = user_id

