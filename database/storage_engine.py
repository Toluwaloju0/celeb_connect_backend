""" a module to provide connection to MySql database for user storage and queries """

from os import getenv
from sqlalchemy import create_engine, select
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
        from models.refresh_token_model import RefreshToken

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
            return function_response(True, token_object.to_dict())
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

    def get_otp_email_object(self, code: str):
        """ a method to query the database based on the code provided
        Args:
            code (str): the code to be queried for
        Return the otp object found with the provided code
        """

        otp_object = self.__session.scalars(select(OtpCode).where(OtpCode.code == code)).one_or_none()
        if otp_object:
            return function_response(True, otp_object)
        return function_response(False)
    



    def close(self):
        self.__session.flush()

        self.__session.close()

storage = DBStorage()
storage.create_tables()
