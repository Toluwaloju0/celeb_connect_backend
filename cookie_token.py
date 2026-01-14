""" a module to get and save tokens to be used as access and refresh tokens"""

from os import getenv
import jwt
from datetime import datetime, timedelta

from models.refresh_token_model import RefreshToken
from utils.responses import function_response
from database.storage_engine import storage

class Token:
    """The token class for all my token activities"""

    def __init__(self):
        """ the initializer for the class"""
        self.__access_secret = getenv("JWT_ACCESS_KEY")
        self.__refresh_secret = getenv("JWT_REFRESH_KEY")

    def create_access_token(self, user_id):
        """ a method to create the access token for the user
        Args:
            user_id (ObjectId): the user id of the user which would be used in the token creation
        Return the token as part of the response
        """

        token = jwt.encode({
            "user_id": str(user_id),
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(minutes=5)
        }, self.__access_secret, algorithm="HS256")

        return function_response(True, {"access_token": token})
    
    def verify_access_token(self, access_token):
        """
        a method to verify the access token
        Args:
            access_token (str): the access token to verify
        Return a response containing the user object from the database
        """

        try:
            payload = jwt.decode(access_token, self.__access_secret, algorithms="HS256")
            user_id = payload.get("user_id")
            get_user_response = storage.get_user_by_id(user_id)
            return get_user_response
        except jwt.ExpiredSignatureError:
            return function_response(True)
        
    def create_refresh_token(self, user_id: str):
        """ a method to create the refresh token
        Args:
            email: the email associated with the token
        """

        token = jwt.encode({
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(seconds=30)
        }, self.__refresh_secret, algorithms="HS256")
        # create the refresh token class before saving it to the database
        refresh_object = RefreshToken(token, user_id)
        try:
            refresh_object.save()
            return function_response(True, {"refresh_token": token})
        except Exception as e:
            return function_response(False)
    
    def verify_refresh_token(self, token: str):
        """ a method to verify the refresh token passed to the user
        Args:
            token (str): the token to be used to refresh the user status
        Return the user email as part of the response
        """

        user_id_response = storage.get_refresh_token(token)
        return user_id_response

token_manager = Token()