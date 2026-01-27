""" a module to define user routes """

from fastapi import Depends, APIRouter, Body
from fastapi.responses import JSONResponse
from typing import Dict
from argon2.exceptions import VerifyMismatchError
from pydantic import EmailStr

from utils.responses import api_response
from utils.check_password import ph, check_password_strength
from utils.check_email import check_email
from middlewares.get_user_from_cookies import get_user_from_access_token
from database.storage_engine import storage

user = APIRouter(prefix="/user", tags=["Users"], dependencies=[Depends(get_user_from_access_token)])

@user.get("/me")
def get_me(user_response = Depends(get_user_from_access_token)):
    """ a endpoint to get the user object from the database
    Args:
        user_response: the response gotten from the access token
    """

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content - api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user = user_response.payload

    content = api_response(True, "The user has been retrieved successfully", user.to_dict())
    return JSONResponse(content.model_dump  ())

@user.patch("/me/password")
def update_password(payload: Dict[str, str] = Body(), user_response = Depends(get_user_from_access_token)):
    """ a endpoint to update the user password """

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content - api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user, old_password, new_password = user_response.payload, payload.get("old_password"), payload.get("new_password")

    if not old_password or not new_password:
        content = api_response(False, "The old and new passwords must be provided")
        return JSONResponse(content.model_dump(), 500)
    if old_password == new_password:
        content = api_response(False, "The old and new password must be different")
        return JSONResponse(content.model_dump(), 500)
    
    try:
        ph.verify(user.password, old_password)
    except VerifyMismatchError:
        content = api_response(False, "the old password does not match the user password")
        return JSONResponse(content.model_dump(), 500)
    
    check_password_response = check_password_strength(new_password)
    if not check_password_response.status:
        content = api_response(False, "The password provided does not match the required strength")
        return JSONResponse(content.model_dump(), 500)
    
    user.password = ph.hash(new_password)
    user.save()

    content = api_response(True, "The user password has been updated", user.to_dict())
    return JSONResponse(content.model_dump())

@user.patch("/me/email")
def update_email(payload: Dict[str, EmailStr] = Body(), user_response=Depends(get_user_from_access_token)):
    """The endpoint to update the user email address """

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content - api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user, new_email = user_response.payload, payload.get("new_email")

    if not new_email:
        content = api_response(False, "The new email address must be provided")
        return JSONResponse(content.model_dump(), 500)
    
    check_email_response = check_email(new_email)
    if not check_email_response.status:
        content = api_response(False, "The provided email address is not up to the required standard")
        return JSONResponse(content.model_dump(), 500)
    
    user.email = new_email
    user.is_verified = False
    user.save()

    content = api_response(True, "The user email has been updated successfully", user.to_dict())
    return JSONResponse(content.model_dump())

@user.put("/me/update")
def update_me(payload: Dict[str, str] = Body(), user_response = Depends(get_user_from_access_token)):
    """ an endpoint to update a user instance by changing the name or phone number"""

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user, update = user_response.payload, False
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")
    phone_number = payload.get("phone_number")

    name = user.name.split(" ")
    if first_name:
        name[0] = first_name
    if last_name:
        name[1] = last_name
    name = f"{name[0]} {name[1]}"
    if name != user.name:
        update = True
        user.name = name
    if phone_number:
        update = True
        user.phone_number = phone_number

    if update:
        user.save()
        content = api_response(True, "The user has been updated successfully", user.to_dict())
    else:
        content = api_response(True, "Nothing was updated", user.to_dict())
    return JSONResponse(content.model_dump())

@user.delete("/me")
def delete_me(user_response = Depends(get_user_from_access_token)):
    """ an endpoint to allow the user to delete the account from the database"""

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user = user_response.payload

    user.delete()

    content = api_response(True, "The user has been deleted")
    response = JSONResponse(content.model_dump())
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
