""" a module to define the authentication route """

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from argon2.exceptions import VerifyMismatchError

from models.user import User, UserCreate, UserLogin
from database.storage_engine import storage
from utils.responses import api_response
from utils.cookie_token import token_manager
from utils.check_email import check_email
from utils.check_password import check_password_strength, ph

auth = APIRouter(tags=["Authentication"], prefix="/auth")

@auth.post("/signup")
async def signup(user: UserCreate):
    """ a function to sign a new user to use the web app"""

    existing_user = storage.get_user_from_email(user.email)
    if existing_user.status:
        # the user exists so the user should login instead of signing up again
        content = api_response(False, "The user exists")
        response = JSONResponse(content.model_dump())
        return response
    
    # implement more checks here for the user
    # check the user email
    email_check_response = check_email(user.email)
    if not email_check_response.status:
        content = api_response(False, "The email does not have a valid domain")
        return JSONResponse(content.model_dump())
    
    # check the strength of the password
    password_strength_response = check_password_strength(user.password)
    if not password_strength_response.status:
        content = api_response(False, "The password does not reach the minimum password strength requirement")
        return JSONResponse(content.model_dump())
    
    # send an email to the user for otp verification


    # create the user
    user = User(**user.model_dump())
    user.password = ph.hash(user.password)
    user.save()

    # set the cookies and send them to the user frontend
    access_tokesn_response = token_manager.create_access_token(user.id)
    refresh_token_response = token_manager.create_refresh_token(user.id)
    # create the refresh token for user refresh
    content = api_response(True, "The user has been created", user.to_dict())
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_tokesn_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("refresh_token"))
    return response


@auth.post("/login")
def login(user: UserLogin):
    """ a function to log the user to the api and website
    Args:
        user: the user information containing the email and password
    """

    saved_user_response = storage.get_user_from_email(user.email, user.password)
    if not saved_user_response.status:
        # return a response that the user is not found
        content = api_response(False, "No user is found for the current email address")
        return JSONResponse(content.model_dump())
    
    user = saved_user_response.payload

    access_token_response = token_manager.create_access_token(user.get("id"))
    refresh_token_response = token_manager.create_refresh_token(user.get("id"))
    content = api_response(True, "Login successful", user)
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("refresh_token"))
    return response

# a route to validate the account