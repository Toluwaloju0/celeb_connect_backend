""" a module to provide connection to MySql database for user storage and queries """

from os import getenv
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session
from argon2.exceptions import VerifyMismatchError

from models.user import User
from models.refresh_token_model import RefreshToken
from models.otp_codes_model import OtpCode
from utils.responses import function_response
from utils.check_password import ph

class DBStorage:
    """ The storage class with a connection to mysql for storage """

    def __init__(self):
        """ a method to create the database connection string """

        db_name, db_host, db_pwd = getenv("DB_NAME"), getenv("DB_HOST"), getenv("DB_PASSWORD")
        db_port, db_user = getenv("DB_PORT"), getenv("DB_USER")

        self.__engine = create_engine(f"mysql+mysqldb://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}")
        self.__session = Session(bind=self.__engine, expire_on_commit=False)


    def create_tables(self):
        """ A method to create the database tabless """

        from models.base_model import Base
        from models.user import User
        from models.otp_codes_model import OtpCode
        from models.refresh_token_model import RefreshToken, AgentRefresh
        from models.agent_model import Agent
        from models.celebrity_model import Celeb

        Base.metadata.create_all(self.__engine)

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

        user = self.__session.scalars(select(User).where(User.id == user_id)).one_or_none()

        if not user:
            return function_response(False)
        return function_response(True, user)


    def get_refresh_token(self, token: str):
        """ 
        a method to save the token provided while associating it with the user id
        Args:
            token (str): the token to be saved
        """

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

        otp_object = self.__session.scalars(select(OtpCode).where(OtpCode.code == code)).one_or_none()
        if otp_object:
            return function_response(True, otp_object)
        return function_response(False)
    
    def get_admin_from_email(self, email, password = None):
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
        
    def get_agent_from_id(self, agent_id: str):
        """ a method to get the agent from the agent id provided
        Args:
            agent_id: the id of the agent
        """

        from models.agent_model import Agent

        agent = self.__session.scalars(select(Agent).where(Agent.id == agent_id)).one_or_none()

        return function_response(True, agent) if agent else function_response(False)
    
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

        # agent_refresh = self.__session.scalars(select(AgentRefresh).where(AgentRefresh.agent_id == agent_id)).one_or_none()
        # if agent_refresh:
        #     agent_refresh.delete()

    def close(self):
        self.__session.flush()

        self.__session.close()

storage = DBStorage()
storage.create_tables()
