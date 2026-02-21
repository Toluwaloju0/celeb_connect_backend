""" a module to create the database tables for the application """


def create_tables():
    from  middlewares.session_middleware import engine
    from models.base_model import Base
    from models.user import User
    from models.refresh_token_model import RefreshToken, AgentRefresh
    from models.otp_codes_model import OtpCode
    from models.celebrity_model import Celeb
    from models.booking_model import Booking
    from models.avalilability_model import Availability
    from models.agent_model import Agent
    from models.admin_model import Admin

    Base.metadata.create_all(engine)