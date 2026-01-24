""" a module to define the refresh token model for saving refresh tokens """

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Basemodel, Base

class RefreshToken(Basemodel, Base):
    """ the refresh token class """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(String(60), ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_token")

    def __init__(self, user_id):
        """ the initializer for the refresh token object"""

        super().__init__()

        self.user_id = user_id

class AgentRefresh(Basemodel, Base):
    """ The class for the admin refresh token """

    __tablename__ = "agent_refresh"

    agent_id: Mapped[str] = mapped_column(String(60), ForeignKey("agents.id"))

    agent: Mapped["Agent"] = relationship(back_populates="refresh_token")

    def __init__(self, agent_id):
        """ the class initializer
        Args:
            agent_id: the agent id
        """

        super().__init__()
        self.agent_id = agent_id
