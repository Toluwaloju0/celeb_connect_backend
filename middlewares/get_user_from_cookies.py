""" a module to define a middle ware which gets the user from the access token provided """

from fastapi import Request

from utils.cookie_token import token_manager

def get_user_from_access_token(request: Request):
    """ a method to define a middle ware which gets the user from the access token provided """

    access_token = request.cookies.get("access_token")

    verify_token_response = token_manager.verify_access_token(access_token)

    return verify_token_response