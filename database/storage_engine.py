""" a module to provide connection to MySql database for user storage and queries """

from os import getenv
from sqlalchemy import create_engine, select, delete, func
from sqlalchemy.orm import Session
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends

from utils.responses import function_response
from utils.check_password import ph

class DBStorage:
    """ The storage class with a connection to mysql for storage """

    def __init__(self, session: Session):
        """ a method to create the database connection string """

        self.__session = session

    def save(self, obj):
        """ a method to save the objects to the database """
        self.__session.add(obj)
        self.__session.commit()

    def get_user_from_email(self, email: str, password: str | None=None):
        """a method to get the user using the provided email address
        Args:
            email(str): the email address of the user

        """
        from models.user import User
        user = self.__session.scalars(select(User).where(User.email == email)).one_or_none()
        if user:
            if password:
                try:
                    ph.verify(user.password, password)
                except VerifyMismatchError:
                    return function_response(False)
            return function_response(True, user)
        return function_response(False)
    
    def get_user_by_id(self, user_id: str):
        """ a method to get the user using the provided user id"""

        from models.user import User

        user = self.__session.scalars(select(User).where(User.id == user_id)).one_or_none()

        return function_response(True, user) if user else function_response(False)


    def get_refresh_token(self, token: str):
        """ 
        a method to save the token provided while associating it with the user id
        Args:
            token (str): the token to be saved
        """

        from models.refresh_token_model import RefreshToken


        token_object = self.__session.scalars(select(RefreshToken).where(RefreshToken.id == token)).one_or_none()
        if token_object:
            return function_response(True, token_object)
        return function_response(False)
    
    def get_otp_object(self, email_address):
        """ a method to get an otp object so that it can be updated and resaved to the database
        Args:
            email_address (str): the email address containing the otp code
        Return the otp object along with the response
        """

        from models.otp_codes_model import OtpCode


        otp_object = self.__session.scalars(select(OtpCode).where(OtpCode.email == email_address)).one_or_none()
        if not otp_object:
            return function_response(False)
        return function_response(True, otp_object)
    
    def delete(self, object):
        """ a method to delete otp codes from the application"""

        self.__session.delete(object)
        self.__session.commit()

    def get_otp_email(self, code: str):
        """ a method to query the database based on the code provided
        Args:
            code (str): the code to be queried for
        Return the otp object found with the provided code
        """

        from models.otp_codes_model import OtpCode


        otp_object = self.__session.scalars(select(OtpCode).where(OtpCode.code == code)).one_or_none()
        if otp_object:
            return function_response(True, otp_object)
        return function_response(False)
    
    def get_admin_from_email(self, email, password):
        """ a method to get the admin from the database using the email address
        Args:
            email: the email of the admin in the database
        """

        from models.admin_model import Admin

        admin = self.__session.scalars(select(Admin).where(Admin.email == email)).one_or_none()
        if not admin:
            return function_response(False)
        try:
            ph.verify(admin.password, password)
            return function_response(True, admin)
        except VerifyMismatchError:
            return function_response(False)
    
    
    def get_admin_from_id(self, admin_id):
        """ a method to get the admin from the database using the admin id
        Args:
            admin_id: the id of the admin
        """

        from models.admin_model import Admin

        admin = self.__session.scalars(select(Admin).where(Admin.id == admin_id)).one_or_none()

        return function_response(True, admin) if admin else function_response(False)
    
    def get_admin_from_refresh(self, refresh_token: str):
        """ a method to get the admin from the refresh token provided 
        Args:
            refresh_token: the refresh token to be user
        """

        from models.admin_model import Admin

        admin = self.__session.scalars(select(Admin).where(Admin.refresh_token == refresh_token)).one_or_none()

        return function_response(True, admin) if admin else function_response(False)
    
    def get_agent_from_email(self, email: str, password: str | None = None):
        """ a method to get the agent from the database and verify the password
        Args:
            email (str): the agent email address
            password (str): the agent password
        """

        from models.agent_model import Agent

        agent = self.__session.scalars(select(Agent).where(Agent.email == email)).one_or_none()

        if not agent:
            return function_response(False)
        
        if not password:
            return function_response(True)
        
        try:
            ph.verify(agent.password, password)
            return function_response(True, agent)
        except VerifyMismatchError:
            return function_response(False)
        
    def get_agent_from_id(self, agent_id):
        """ a method to get the agent from the agent id provided
        Args:
            agent_id: the id of the agent
        """

        from models.agent_model import Agent

        agent = self.__session.scalars(select(Agent).where(Agent.id == agent_id)).one_or_none()
        return function_response(True, agent) if agent else function_response(False)
        
    def get_agents(self, offset: int, limit: int):
        """ a method to get the agent from the agent id provided
        Args:
            agent_id: the id of the agent or none when i want to get all the agents for the admin or users
        """

        from models.agent_model import Agent

        agents = self.__session.scalars(select(Agent).offset(offset).limit(limit)).all()
        my_list = []
        if len(agents) > 0:
            for agent in agents:
                my_list.append(agent.to_dict())
            return function_response(True, my_list)
        return function_response(False)

    def get_agent_id_from_refresh(self, token):
        """ a method to get the agent refresh token
        Args:
            token (str): the token to be queried for
        """
        from models.refresh_token_model import AgentRefresh

        agent_id = self.__session.scalars(select(AgentRefresh.agent_id).where(AgentRefresh.id == token)).one_or_none()
        return function_response(True, {"agent_id": agent_id}) if agent_id else function_response(False)
    
    def delete_agent_refresh_token(self, agent_id):
        """a method to delete all the agent refresh token for the agent with that id
        Args:
            agent_id: the agent id with the reference to the agent_id column
        """

        from models.refresh_token_model import AgentRefresh

        self.__session.execute(delete(AgentRefresh).where(AgentRefresh.agent_id == agent_id))
        self.__session.commit()

    def get_celebrities(
            self,
            agent_id: str,
            limit: int,
            offset: int,
            celeb_id: str | None = None
    ):
        """ a method to get the celebrities on a given agent
        Args:
            agent_id: the agent is of the celebrities
            limit: the dataset limit
            offset: the amount of data to skip
            celeb_id: the id of the celebrity to get if founc
        """

        from models.celebrity_model import Celeb

        if celeb_id:
            celeb = self.__session.scalars(select(Celeb).where(Celeb.agent_id == agent_id).where(Celeb.id == celeb_id)).one_or_none()

            return function_response(True, celeb.to_dict()) if celeb else function_response(False)
        
        celeb_list = []
        celebs = self.__session.scalars(select(Celeb).where(Celeb.agent_id == agent_id).offset(offset).limit(limit)).all()
        if len(celebs) > 0:
            for celeb in celebs:
                celeb_list.append(celeb.to_dict())
        else:
            return function_response(False)
        
        return function_response(True, celeb_list)
    
    def get_celeb_by_id(self, celeb_id: str):
        """ a method to get the celebrity from the provided celeb id
        Args:
            celeb_id (str): the celebrity id
        """

        from models.celebrity_model import Celeb

        if not celeb_id:
            return function_response(False)
        
        celeb = self.__session.scalars(select(Celeb).where(Celeb.id == celeb_id)).one_or_none()
        return function_response(True, celeb) if celeb else function_response(False)
    
    def get_celebrities_for_admin(self, limit: int, offset: int):
        """ a method to get all the celebrities for the admin
        Args:
            limit: the limit of data to be gotten
            offset: the amount of data to be skipped
        """

        from models.celebrity_model import Celeb

        celebs = self.__session.scalars(select(Celeb).limit(limit).offset(offset)).all()
        my_list = [celeb.to_dict() for celeb in celebs]

        return function_response(True, my_list) if len(my_list) > 0 else function_response(False)
    
    def get_users_for_admin(self, limit, offset):
        """ a method to get the users of the app for the admin dashboard
        Args:
            limit: the limit of the request
            offset: the amount of data to jump over in the database
        """
        
        from models.user import User

        users = self.__session.scalars(select(User).limit(limit).offset(offset)).all()

        my_list = [user.to_dict() for user in users]
        return function_response(True, my_list) if len(my_list) > 0 else function_response(False)
    
    def get_celeb_availability(self, celeb_id):
        """a method to get the availabliity of a celebrity
        Args:
            celeb_id: the id of the celebrity
        """

        from models.avalilability_model import Availability

        availability = self.__session.scalars(select(Availability).where(Availability.celeb_id == celeb_id)).one_or_none()

        return function_response(True, availability) if availability else function_response(False)
    
    def get_user_bookings_info(self, user_id):
        """ a method to get the infor of a users bookings including the count of the approved and rejected bookings
        Args:
            user_id: the user id of the user
        """

        from models.booking_model import Booking, Status

        booking_count = self.__session.execute(select(func.count()).select_from(Booking).where(Booking.user_id == user_id)).scalar()
        successful_booking = self.__session.execute(select(func.count()).select_from(Booking).where(Booking.user_id == user_id).where(Booking.status == Status.APPROVED)).scalar()
        pending_booking = self.__session.execute(select(func.count()).select_from(Booking).where(Booking.user_id == user_id).where(Booking.status == Status.PENDING)).scalar()

        return function_response(True, {"total": booking_count, "success": successful_booking, "pending": pending_booking})
    
    def get_booking(self, booking_id:str = None, limit=10, offset=10, **kwargs):
        """a method to get the booking from the database for either agent or user
        Args:
            booking_id: the booking id to get if none is provided all bookings made by the user or the agent is provided
            kwargs: the user id or agent id should be present in kwargs
        """

        from models.booking_model import Booking

        if "user_id" in kwargs.keys():
            if booking_id:
                booking = self.__session.scalars(select(Booking).where(Booking.id == booking_id).where(Booking.user_id == kwargs["user_id"])).one_or_none()
                return function_response(True, booking) if booking else function_response(False)
            bookings = self.__session.scalars(select(Booking).where(Booking.user_id == kwargs["user_id"]).limit(limit).offset(offset)).all()
        elif "celeb_id" in kwargs.keys():
            if booking_id:
                booking = self.__session.scalars(select(Booking).where(Booking.id == booking_id).where(Booking.celeb_id == kwargs["celeb_id"])).one_or_none()
                return function_response(True, booking) if booking else function_response(False)
            bookings = self.__session.scalars(select(Booking).where(Booking.celeb_id == kwargs["celeb_id"]).limit(limit).offset(offset)).all()
        else:
            return function_response(False)
        booking_list = [booking.to_dict() for booking in bookings]
        return function_response(True, booking_list) if len(booking_list) > 0 else function_response(False)
    
    def get_booking_by_id(self, booking_id):
        """ a method to get the booking for an admin to approve
        Args:
            booking_id: the booking id to search for
        """

        from  models.booking_model import Booking

        booking = self.__session.scalars(select(Booking).where(Booking.id == booking_id)).one_or_none()

        return function_response(True, booking) if booking else function_response(False)
    
    def get_celeb_bookings(self, celeb_id: str, limit: int, offset: int):
        """ a method to get the bookings of a celeb
        Args:
            celeb_id: the celebrity id
        """

        from models.booking_model import Booking

        if not celeb_id:
            return function_response(False)
        
        bookings = self.__session.scalars(select(Booking).where(Booking.celeb_id == celeb_id).limit(limit).offset(offset))

        my_list = [booking.to_dict() for booking in bookings]

        return function_response(True, my_list) if len(my_list) > 0 else function_response(False)
    
    def rollback(self):
        """
        Docstring for rollback
        
        :param self: Description
        """

        self.__session.rollback()

    def close(self):
        self.__session.flush()

        self.__session.close()
