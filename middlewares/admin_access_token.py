""" a module to define a middle ware for getting the admin from the provided access token """

from fastapi import Request

from utils.responses import function_response
from utils.cookie_token import token_manager

def get_admin_from_access_token(request: Request):
    """ a function to get the access token and confirm if the admin is the one logging in to the application 
    Args:
        request: the request from the frontend
    """

    access_token = request.cookies.get("access_token")
    return token_manager.verify_admin_access_token(access_token, request.state.storage)
