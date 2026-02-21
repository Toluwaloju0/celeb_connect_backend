""" a module to define the authentication route """

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from models.user import User, UserCreate, UserLogin, UserLevel
from models.otp_codes_model import OTPRequest
from models.admin_model import AdminLogin
from models.agent_model import AgentLogin
from database.storage_engine import DBStorage
from utils.responses import api_response
from utils.cookie_token import token_manager
from utils.check_email import check_email
from utils.check_password import check_password_strength, ph
from middlewares.get_user_from_cookies import get_user_from_access_token
from middlewares.admin_access_token import get_admin_from_access_token
from middlewares.agent_access_token import verify_agent_access_token
from services.email_sender import email_sender
from utils.id_string import uuid
from utils.delete_refresh_token import delete_refresh_token

auth = APIRouter(tags=["Authentication"], prefix="/auth")

@auth.post("/signup")
async def signup(user: UserCreate, request: Request):
    """ a function to sign a new user to use the web app"""

    storage: DBStorage = request.state.storage

    existing_user = storage.get_user_from_email(user.email)
    if existing_user.status:
        # the user exists so the user should login instead of signing up again
        content = api_response(False, "The user exists")
        response = JSONResponse(content.model_dump(), 500)
        return response
    
    # implement more checks here for the user
    # check the user email
    email_check_response = check_email(user.email)
    if not email_check_response.status:
        content = api_response(False, "The email does not have a valid domain")
        return JSONResponse(content.model_dump(), 500)
    
    # check the strength of the password
    password_strength_response = check_password_strength(user.password)
    if not password_strength_response.status:
        content = api_response(False, "The password does not reach the minimum password strength requirement")
        return JSONResponse(content.model_dump(), 500)
    
    # send an email to the user for otp verification


    # create the user
    user = User(**user.model_dump())
    user.password = ph.hash(user.password)
    user.save(storage)

    # set the cookies and send them to the user frontend
    access_tokesn_response = token_manager.create_access_token(user.id)
    refresh_token_response = token_manager.create_refresh_token(user.id, storage)
    # create the refresh token for user refresh
    content = api_response(True, "The user has been created", user.to_dict())
    response = JSONResponse(content.model_dump(), 201)
    response.set_cookie("access_token", access_tokesn_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("refresh_token"))
    return response


@auth.post("/login")
async def login(user: UserLogin, request: Request):
    """ a function to log the user to the api and website
    Args:
        user: the user information containing the email and password
    """

    storage: DBStorage = request.state.storage

    saved_user_response = storage.get_user_from_email(user.email, user.password)
    if not saved_user_response.status:
        # return a response that the user is not found
        content = api_response(False, "No user is found for the current email address and password")
        return JSONResponse(content.model_dump(), 500)
    
    user = saved_user_response.payload

    access_token_response = token_manager.create_access_token(user.id)
    refresh_token_response = token_manager.create_refresh_token(user.id, storage)
    content = api_response(True, "Login successful", user.to_dict())
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("refresh_token"))
    return response

@auth.get("/otp/request")
async def request_otp_code(request: Request, user_response = Depends(get_user_from_access_token)):
    """ a method to send the required otp code to the user and save the code to the database
    Args:
        user_response: the response of the databbase return of the id in the access token
    
    Return a dictionary with true or false upon successful sending of the otp code
    """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The user is not found")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The access code is expired")
        return JSONResponse(content.model_dump(), 205)
    
    if user_response.payload.is_verified:
        # the user is already verified so no otp code can be requested again
        content = api_response(True, "This user is already verified", user_response.payload.to_dict())
        return JSONResponse(content.model_dump())
    
    send_mail_response = email_sender.send_otp_code(user_response.payload.email, storage)

    if not send_mail_response.status:
        content = api_response(False, "The email message was not sent successfully")
        return JSONResponse(content.model_dump(), 500)
    content = api_response(True, "The mail was successfully sent, Check your email for the code")
    return JSONResponse(content.model_dump())


@auth.post("/otp/validate")
async def validate_otp(otp_code: OTPRequest, request: Request, user_response = Depends(get_user_from_access_token)):
    """ a function to validate user otp codes so as to activate their provided email as valid"""

    storage: DBStorage = request.state.storage

    otp_code = otp_code.otp_code
    if not user_response.status:
        content = api_response(False, "The user is not found")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The access code is expired")
        return JSONResponse(content.model_dump(), 205)
    
    user_email_response = storage.get_otp_email(otp_code)
    user = user_response.payload

    if not user_email_response.status:
        content = api_response(False, "The OTP code is invalid")
        return JSONResponse(content.model_dump(), 500)
    
    if user_email_response.payload.email != user.email:
        content = api_response(False, "Your email address does not correspond with the provided otp code")
        return JSONResponse(content.model_dump(), 500)
    
    user_email_response.payload.delete(storage)
    
    # update the user from this end and delete the otp code
    user.is_verified = True
    if user.old_level == UserLevel.UNVERIFIED:
        user.old_level = UserLevel.VERIFIED
        user.level = UserLevel.VERIFIED
    else:
        user.level = user.old_level
    user.save(storage)
    
    
    content = api_response(True, "The user has been validated successfully", user.to_dict())
    return JSONResponse(content.model_dump())

@auth.post("/logout")
async def logout(request: Request, user_response = Depends(get_user_from_access_token)):
    """ a method to log a user out from the connection by deleting the access and refresh tokens """

    if not user_response.status:
        content = api_response(False, "The user is not found")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The access code is expired")
        return JSONResponse(content.model_dump(), 205)
    
    # delete the refresh token from the database
    delete_refresh_token(request.cookies.get("refresh_token"), request.state.storage)

    content = api_response(True, "Log out successful")
    response = JSONResponse(content.model_dump())
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response

@auth.get("/token/refresh")
async def refresh_token(request: Request):
    """ a function to refresh the access token if it has expire
    Args:
        request: the request context from fastapi
    """

    storage: DBStorage = request.state.storage

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        content = api_response(False, "The refresh token is not provided, login and try again")
        return JSONResponse(content.model_dump(), 500)
    
    verify_refresh_response = token_manager.verify_refresh_token(refresh_token, storage)
    if not verify_refresh_response.status:
        content = api_response(False, "The provided token does not match a user on our end")
        return JSONResponse(content.model_dump(), 500)
    
    token_object = verify_refresh_response.payload
    user_id = token_object.user_id

    access_token_response = token_manager.create_access_token(user_id)
    refresh_token_response = token_manager.create_refresh_token(user_id, storage)

    token_object.delete(storage)
    content = api_response(True, "The refresh is successful")
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("refresh_token"))
    return response

@auth.post("/admin/login")
async def admin_login(admin: AdminLogin, request: Request):
    """ a endpoint to log an admin into the application
    Args:
        the admin email and password in the request body
    """

    storage: DBStorage = request.state.storage

    admin_user_response = storage.get_admin_from_email(admin.email, admin.password)
    if not admin_user_response.status:
        content = api_response(False, "Login unsuccessful check your password and email and try again")
        return JSONResponse(content.model_dump(), 500)
    
    AdminUser = admin_user_response.payload
    
    access_token_response = token_manager.create_access_token(AdminUser.id)
    AdminUser.refresh_token = uuid()
    AdminUser.save(storage)

    content = api_response(True, "The admin logged in successfully", AdminUser.to_dict())
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", AdminUser.refresh_token)
    return response

@auth.get("/admin/refresh")
async def refresh_admin_token(request: Request):
    """ a method to refresh the admin token
    Args:
        request: the frontend request
    """
    storage: DBStorage = request.state.storage
    refresh_token = request.cookies.get("refresh_token")

    admin_user_response = storage.get_admin_from_refresh(refresh_token)
    if not admin_user_response.status:
        content = api_response(False, "The refresh token is not valid")
        return JSONResponse(content.model_dump(), 500)
    
    AdminUser = admin_user_response.payload
    
    AdminUser.refresh_token = uuid()
    AdminUser.save(storage)
    access_token_response = token_manager.create_access_token(AdminUser.id)

    content = api_response(True, "The refresh is successful")
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", AdminUser.refresh_token)
    return response

@auth.post("/admin/logout")
async def log_out_admin(request: Request, admin_response = Depends(get_admin_from_access_token)):
    """ an endpoint to log out an admin from the application """

    if not admin_response.status:
        content = api_response(False, "User not allowed to perform this operation")
        return JSONResponse(content.model_dump(), 401)
    
    if not admin_response.payload:
        content = api_response(False, "Please refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    AdminUser = admin_response.payload
    AdminUser.refresh_token = None
    AdminUser.save(request.state.storage)

    content = api_response(True, "Logout successful")
    response = JSONResponse(content.model_dump())
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@auth.post("/agent/login")
async def agent_login(agent: AgentLogin, request: Request):
    """ an endpoint to log an agent to the route
    Args:
        agent: the agent email and password
    """

    storage: DBStorage = request.state.storage

    get_agent_response = storage.get_agent_from_email(agent.email, agent.password)

    if not get_agent_response.status:
        content = api_response(False, "The provided email and password are not correct")
        return JSONResponse(content.model_dump(), 500)
    
    if not get_agent_response.payload:
        content = api_response(False, "No password is provided")
        return JSONResponse(content.model_dump(), 500)
    
    agent = get_agent_response.payload

    access_token_response = token_manager.create_access_token(agent.id)
    refresh_token_response = token_manager.create_agent_refresh(agent.id, storage)

    content = api_response(True, "Login successful", agent.to_dict())
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("id"))
    return response

@auth.get("/agent/refresh")
async def refresh_agent_token(request: Request):
    """a endpoint to refresh the access and refresh token passed to the user for queries 
    Args:
        request: the request context from the fronted
    """

    storage: DBStorage = request.state.storage
    refresh_token = request.cookies.get("refresh_token")

    agent_id_response = token_manager.verify_agent_refresh(refresh_token, storage)
    if not agent_id_response.status:
        content = api_response(False, "The refresh token is invalid")
        return JSONResponse(content.model_dump(), 500)
    
    agent_id = agent_id_response.payload.get("agent_id")

    access_token_response = token_manager.create_access_token(agent_id)
    refresh_token_response = token_manager.create_agent_refresh(agent_id, storage)

    content = api_response(True, "Token refresh successful")
    response = JSONResponse(content.model_dump())
    response.set_cookie("access_token", access_token_response.payload.get("access_token"))
    response.set_cookie("refresh_token", refresh_token_response.payload.get("id"))
    return response

@auth.post("/agent/logout")
async def agent_log_out(request: Request, get_agent_response = Depends(verify_agent_access_token)):
    """ an endpoint to log an agent out from the website """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to perform this task")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, please refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    agent = get_agent_response.payload

    if agent.refresh_token:
        agent.refresh_token.delete(request.state.storage)

    content = api_response(True, "Log out successful")
    response = JSONResponse(content.model_dump())
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
