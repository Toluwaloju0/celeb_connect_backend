""" a module to define user routes """

from fastapi import Depends, APIRouter, Body, Request
from fastapi.responses import JSONResponse
from typing import Dict
from argon2.exceptions import VerifyMismatchError
from pydantic import EmailStr

from models.celebrity_model import Celeb
from models.booking_model import Booking
from models.avalilability_model import UserWeekDay
from utils.responses import api_response
from utils.check_password import ph, check_password_strength
from utils.check_email import check_email
from utils.booking_price import price_converter
from middlewares.get_user_from_cookies import get_user_from_access_token
from database.storage_engine import DBStorage

user = APIRouter(prefix="/user", tags=["Users"], dependencies=[Depends(get_user_from_access_token)])

@user.get("/me")
async def get_me(user_response = Depends(get_user_from_access_token)):
    """ a endpoint to get the user object from the database
    Args:
        user_response: the response gotten from the access token
    """

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user = user_response.payload

    content = api_response(True, "The user has been retrieved successfully", user.to_dict())
    return JSONResponse(content.model_dump  ())

@user.patch("/me/password")
async def update_password(request: Request, payload: Dict[str, str] = Body(), user_response = Depends(get_user_from_access_token)):
    """ a endpoint to update the user password """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
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
    user.save(storage)

    content = api_response(True, "The user password has been updated", user.to_dict())
    return JSONResponse(content.model_dump())

@user.patch("/me/email")
async def update_email(request: Request, payload: Dict[str, EmailStr] = Body(), user_response=Depends(get_user_from_access_token)):
    """The endpoint to update the user email address """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
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
    user.save(storage)

    content = api_response(True, "The user email has been updated successfully", user.to_dict())
    return JSONResponse(content.model_dump())

@user.put("/me/update")
async def update_me(request: Request, payload: Dict[str, str] = Body(), user_response = Depends(get_user_from_access_token)):
    """ an endpoint to update a user instance by changing the name or phone number"""

    storage: DBStorage = request.state.storage

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
        user.save(storage)
        content = api_response(True, "The user has been updated successfully", user.to_dict())
    else:
        content = api_response(True, "Nothing was updated", user.to_dict())
    return JSONResponse(content.model_dump())

@user.delete("/me")
async def delete_me(request: Request, user_response = Depends(get_user_from_access_token)):
    """ an endpoint to allow the user to delete the account from the database"""

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user = user_response.payload

    user.delete(storage)

    content = api_response(True, "The user has been deleted")
    response = JSONResponse(content.model_dump())
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@user.get("/agents")
@user.get("/agents/{agent_id}")
async def get_agents_and_celebs(request: Request, agent_id: str = None, page:int = 1, limit: int = 10, user_response=Depends(get_user_from_access_token)):
    """ a module for user to get agents from the database 
    when agent_id is given the agent along with the agent celebrities are provided
    Args:
        agent_id: the agent id for the agent to search for
    """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    if not agent_id:
        # no agent id is given so all the agents are provided for the user
        page = 0 if page - 1 < 0 else page - 1
        agents_response = storage.get_agents(page * limit, limit)
        if not  agents_response.status:
            content = api_response(False, "No agent found")
        else:
            agents = agents_response.payload
            content = api_response(True, "Agents retrieved successfully", agents)
        return JSONResponse(content.model_dump())
    
    agent_response = storage.get_agent_from_id(agent_id)
    if not agent_response.status:
        content = api_response(False, "No agent is found with the provided id")
        return JSONResponse(content.model_dump())
    
    agent = agent_response.payload
    celeb_list = [celeb.to_dict() for celeb in agent.celebs]

    content = api_response(True, "Agent and celebrities gotten", {"agent": agent.to_dict(), "celebs": celeb_list})
    return JSONResponse(content.model_dump())

@user.get("/celeb/{celeb_id}/availability")
async def get_celeb_availability(celeb_id:str, request: Request, user_response = Depends(get_user_from_access_token)):
    """ an endpoint to get the availablity of a celebrity using the celebrity provided id 
    Args:
        celeb_id: the provided celebrity id for the celeb
        user_response: the user from the access token
    """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)

    availability_response = storage.get_celeb_availability(celeb_id)
    if not availability_response.status:
        content = api_response(False, "No availability for the selected celebrity")
    else:
        content = api_response(True, "Availability gotten successfully", availability_response.payload.to_dict())
    return JSONResponse(content.model_dump())

@user.post("/{celeb_id}/book")
async def book_a_celeb(celeb_id: str, payload: UserWeekDay, request: Request, user_response=Depends(get_user_from_access_token)):
    """ an endpoint to book a celebrity by a user
    Args:
        celeb_id: the celebrity id
    """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user = user_response.payload

    celeb_response = storage.get_celeb_by_id(celeb_id)
    if not celeb_response.status:
        content = (False, "No celebrity found with the provided id")
        return JSONResponse(content.model_dump())
    
    celeb: Celeb = celeb_response.payload

    celeb.bookings.append(Booking(payload.day ,user.id, payload.type))
    celeb.save(storage)

    content = api_response(True, "Booking added")
    return JSONResponse(content.model_dump())

@user.get("/bookings/count")
async def count_all_user_bookings(request: Request, user_response=Depends(get_user_from_access_token)):
    """ an endpoint to get the count of bookings a users has submitted along with approved counts and rejected counts
    Args:
        user_response: the user from the access token
    """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)
    
    user = user_response.payload
    
    count_response = storage.get_user_bookings_info(user.id)
    if not count_response.status:
        content = api_response(False, "The user id is not correct")
    else:
        content = api_response(True, "Count gotten", count_response.payload)
    return JSONResponse(content.model_dump())
    

@user.get("/bookings")
@user.get("/bookings/{booking_id}")
async def get_bookings_for_user(request: Request, booking_id: str = None, page: int = 1, limit: int = 10, user_response=Depends(get_user_from_access_token)):
    """ an endpoint to get all the bookings of a user and view the booking status
    Args:
        booking_id: the booking ticket number for viewing the booking by the user
        page: the booking page on the front end
        limit: the amount of data to be viewed by the frontend
    """

    storage: DBStorage = request.state.storage

    if not user_response.status:
        content = api_response(False, "The access token is not valid")
        return JSONResponse(content.model_dump(), 401)
    
    if not user_response.payload:
        content = api_response(False, "The Token expired, Refresh the token and try again")
        return JSONResponse(content.model_dump(), 205)

    user = user_response.payload

    page = 0 if page - 1 > 0 else page - 1
    booking_list_response = storage.get_booking(booking_id, limit, limit * page, user_id=user.id)

    if not booking_list_response.status:
        content = api_response(False, "No booking is found with the provided number")
        return JSONResponse(content.model_dump())
    
    if not booking_id:
        bookings = booking_list_response.payload
        content = api_response(True, "bookings are retrieved successfully", bookings)
        return JSONResponse(content.model_dump())
    
    booking = booking_list_response.payload

    booking_dict = booking.to_dict()

    booking_dict["price"] = price_converter(booking.type)

    content = api_response(True, "Booking is retrieved successfully", booking_dict)
    return JSONResponse(content.model_dump())