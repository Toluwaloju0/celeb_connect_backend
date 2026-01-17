""" a module to define the authentication route """

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from argon2.exceptions import VerifyMismatchError

from models.user import User, UserCreate, UserLogin, UserLevel
from database.storage_engine import storage
from utils.responses import api_response
from utils.cookie_token import token_manager
from utils.check_email import check_email
from utils.check_password import check_password_strength, ph
from middlewares.get_user_from_cookies import get_user_from_access_token
from services.email_sender import email_sender

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
        content = api_response(False, "No user is found for the current email address and password")
        return JSONResponse(content.model_dump())
    
    user = saved_user_response.payload

    access_token_response = token_manager.create_access_token(user.id)
    refresh_token_response = token_manager.create_refresh_token(user.id)
    content = api_response(True, "Login successful", user.to_dict())
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("refresh_token"))
    return response

@auth.get("/otp/request")
def request_otp_code(user_response = Depends(get_user_from_access_token)):
    """ a method to send the required otp code to the user and save the code to the database
    Args:
        user_response: the response of the databbase return of the id in the access token
    
    Return a dictionary with true or false upon successful sending of the otp code
    """

    if not user_response.status:
        content = api_response(False, "The user is not found")
        return JSONResponse(content.model_dump())
    
    if not user_response.payload:
        content = api_response(False, "The access code is expired")
        return JSONResponse(content.model_dump())
    
    if user_response.payload.is_verified:
        # the user is already verified so no otp code can be requested again
        content = api_response(True, "This user is already verified", user_response.payload.to_dict())
        return JSONResponse(content.model_dump())
    
    send_mail_response = email_sender.send_otp_code(user_response.payload.email)

    if not send_mail_response.status:
        content = api_response(False, "The email mail was not sent successfully")
        return JSONResponse(content.model_dump())
    content = api_response(True, "The mail was successfully sent, Check your email for the code")
    return JSONResponse(content.model_dump())


@auth.post("/otp/validate")
def validate_otp(code: str, user_response = Depends(get_user_from_access_token)):
    """ a function to validate user otp codes so as to activate their provided email as valid"""

    if not user_response.status:
        content = api_response(False, "The user is not found")
        return JSONResponse(content.model_dump())
    
    if not user_response.payload:
        content = api_response(False, "The access code is expired")
        return JSONResponse(content.model_dump())
    
    user_email_response = email_sender.get_otp_email(code)
    user = user_response.payload

    if not user_email_response.status:
        content = api_response(False, "The OTP code is invalid")
        return JSONResponse(content.model_dump())
    
    if user_email_response.payload.email != user.email:
        content = api_response(False, "Your email address does not correspond with the provided otp code")
        return JSONResponse(content.model_dump())
    
    user_email_response.payload.delete()
    
    # update the user from this end and delete the otp code
    user.is_verified = True
    user.level = UserLevel.VERIFIED
    user.save()
    
    
    content = api_response(True, "The user has been validated successfully", user.to_dict())
    return JSONResponse(content.model_dump())

@auth.post("/logout")
def logout(user_response = Depends(get_user_from_access_token)):
    """ a method to log a user out from the connection by deleting the access and refresh tokens """

    if not user_response.status:
        content = api_response(False, "The user is not found")
        return JSONResponse(content.model_dump())
    
    if not user_response.payload:
        content = api_response(False, "The access code is expired")
        return JSONResponse(content.model_dump())

    content = api_response(True, "Log out successful")
    response = JSONResponse(content.model_dump())
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response
