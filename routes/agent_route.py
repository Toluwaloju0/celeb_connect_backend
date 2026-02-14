""" a module to define the agent route """

from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Body, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, Optional

from models.agent_model import Agent
from models.celebrity_model import CelebCreate, Celeb
from models.avalilability_model import AgentWeekDay
from models.booking_model import BookingStatus, Status
from database.storage_engine import DBStorage, storage
from middlewares.agent_access_token import verify_agent_access_token
from utils.responses import api_response
from utils.check_password import ph, check_password_strength
from services.file_management import file_manager

agent = APIRouter(prefix="/agent", tags=["Agents"], dependencies=[Depends(verify_agent_access_token)])

@agent.patch("/profile/password")
def update_password(payload: Dict[str, str] = Body(), get_agent_response = Depends(verify_agent_access_token)):
    """ an endpoint to get a new agent password and update the agent password
    This would also verify the agents email address
    
    Args:
        payload: the request body
        get_agent_response: the agent from the access token
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        cotent = api_response(False, "The access token has expired, refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    agent = get_agent_response.payload
    
    old_password, new_password = payload.get("old_password"), payload.get("new_password")
    if not old_password or not new_password or old_password == new_password:
        content = api_response(False, "Both the old and the new password must be provided and must be different")
        return JSONResponse(content.model_dump(), 500)
    
    try:
        ph.verify(agent.password, old_password)
    except VerifyMismatchError:
        content = api_response(False, "The old password does not match the new one")
        return JSONResponse(cotent.model_dump(), 500)
    
    password_strength_checker = check_password_strength(new_password)
    if not password_strength_checker.status:
        content = api_response(False, "The provided password is not up to the required strength")
        return JSONResponse(content.model_dump(), 500)
    
    agent.password = ph.hash(new_password)
    agent.email_verified = True
    agent.save()

    content = api_response(True, "Password update successful", agent.to_dict())
    return JSONResponse(content.model_dump())

@agent.put("/celeb/add")
def add_celebrity(celeb: CelebCreate, get_agent_response = Depends(verify_agent_access_token)):
    """ an endpoint to add a new celeb to the database for this agent """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    agent: Agent = get_agent_response.payload

    agent.celebs.append(Celeb(celeb.name, celeb.location, celeb.profession, celeb.marital_status))
    agent.save()

    celeb = agent.celebs[-1]

    content = api_response(True, "The celebrity has been added successfully", celeb.to_dict())
    return JSONResponse(content.model_dump())

@agent.get("/celebs")
@agent.get("/celebs/{celeb_id}")
def get_celebrity(celeb_id: Optional[str] = None, page: int = 1, offset: int = 10, limit: int = 10, get_agent_response = Depends(verify_agent_access_token)):
    """ a method to get a celebrity infrmation if an celeb_id is given
    else all the celebs of the agents are provided
    Args:
        celeb_id (str): the celeb_id of the celebrity if given
        get_agent_response: the agent in a response
    """

    
    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    agent: Agent = get_agent_response.payload

    # get the celebrities from the database using the required offset and limit
    page = page - 1 if page - 1 > 0 else 0
    celeb_response = storage.get_celebrities(agent.id, limit, offset * page, celeb_id)
    if not celeb_response.status:
        content = api_response(False, "No celebrity is found")
    else:
        content = api_response(True, "Celebrity gotten successfully", celeb_response.payload)
    return JSONResponse(content.model_dump())

@agent.put("/celeb/{celeb_id}/profile/picture")
def add_profile_image(celeb_id: str, file: UploadFile = File(), get_agent_response = Depends(verify_agent_access_token)):
    """ a method to set the celebrity image by the server and save the location to the database
    Args:
        celeb_id (str): the celebrity id
        file: the picture file
        get_agent_response: the agent from the database
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)

    file_type = file.filename.split(".")[-1]

    if not file_type or file_type not in ["png", "jpeg"]:
        content = api_response(False, "The provided file is not in the required format\n\nWe only accept .png or .jpeg files")
        return JSONResponse(content.model_dump(), 500)
    
    get_celeb_response = storage.get_celeb_by_id(celeb_id)
    if not get_celeb_response.status:
        content = api_response(False, "No celebrity found with the provided ID")
        return JSONResponse(content.model_dump(), 500)
    
    saved_file_response = file_manager.save_celeb_file(file)
    if not saved_file_response.status:
        content = api_response(False, "The file was not successfully saved")
        return JSONResponse(content.model_dump(), 500)
    
    celeb: Celeb = get_celeb_response.payload
    file_location = saved_file_response.payload

    if celeb.profile_url:
        file_manager.delete_celeb_file(celeb.profile_url)

    celeb.profile_url = file_location
    celeb.save()

    content = api_response(True, "The upload is successful", celeb.to_dict())
    return JSONResponse(content.model_dump())

@agent.patch("/celeb/{celeb_id}/profile")
def update_celeb_info(celeb_id: str, payload: Dict[str, str] = Body(), get_agent_response = Depends(verify_agent_access_token)):
    """ an endpoint to update the celebrity informations
    Args:
        celeb_id: the celebrity id
        payload: the information to be updated
        get_agent_response: the agent making the update
    """

    
    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    celeb_response = storage.get_celeb_by_id(celeb_id)
    if not celeb_response.status:
        content = api_response(False, "No celebrity found with the provided id")
        return JSONResponse(content.model_dump())
    
    celeb: Celeb = celeb_response.payload

    bio, name, update = payload.get("bio"), payload.get("name"), False

    if bio:
        celeb.bio = bio
        update = True
    if name and name != celeb.name:
        celeb.name = name
        update = True
    if update:
        celeb.save()
        content = api_response(True, "Celebrity information updated successfully", celeb.to_dict())
    else:
        content = api_response(False, "No information to update", celeb.to_dict())
    return JSONResponse(content.model_dump())

@agent.get("/celeb/{celeb_id}/availability")
def get_celeb_availability(celeb_id: str, get_agent_response = Depends(verify_agent_access_token)):
    """an endpoint to get a celeb availability
    Args:
        celeb_id(str): the celebrity id
        get_agent_response: the agent from the access token
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    availability_response = storage.get_celeb_availability(celeb_id)
    if not availability_response.status:
        content = api_response(False, "No availability is found for the provided celeb")
        return JSONResponse(content.model_dump())
    
    content = api_response(True, "Availability found for the celebrity", availability_response.payload.to_dict())
    return JSONResponse(content.model_dump())

@agent.patch("/celeb/{celeb_id}/availability")
def update_celeb_availability(celeb_id: str, payload: AgentWeekDay, get_agent_response = Depends(verify_agent_access_token)):
    """an endpoint to set the availability of a celeb
    Args:
        celeb_id: the id of the celebrity
        payload: a list of the approved days
        get_agent_response: the agent response from the access token
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    availability_response = storage.get_celeb_availability(celeb_id)
    if not availability_response.status:
        content = api_response(False, "no availiability is found for the selected celebrity")
        return JSONResponse(content.model_dump())
    
    availability = availability_response.payload
    if "MONDAY" not in payload.days:
        availability.monday = False
    else:
        availability.monday = True
    if "TUESDAY" not in payload.days:
        availability.tuesday = False
    else:
        availability.tuesday = True
    if "WEDNESSDAY" not in payload.days:
        availability.wednessday = False
    else:
        availability.wednessday = True
    if "THURSDAY" not in payload.days:
        availability.thursday = False
    else:
        availability.thursday = True
    if "FRIDAY" not in payload.days:
        availability.friday = False
    else:
        availability.friday = True

    availability.save()
    content = api_response(True, "Celebrity availability has been updated successfully", availability.to_dict())
    return JSONResponse(content.model_dump())

@agent.get("/celeb/{celeb_id}/bookings")
def get_celeb_bookings(celeb_id: str, page: int = 1, limit:int = 10, get_agent_response = Depends(verify_agent_access_token)):
    """an endpoint to get all the bookings of a celebrity
    Args:
        celeb_id: the celebrity id of which to get the booking
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    page = 0 if page - 1 < 0 else page - 1

    bookings_list_response = storage.get_celeb_bookings(celeb_id, limit, limit * page)
    if not bookings_list_response.status:
        content = api_response(False, "No booking is found for the provided celebrity")
    else:
        content = api_response(True, "Bookings found", bookings_list_response.payload)  

    return JSONResponse(content.model_dump())

@agent.patch("/celeb/{celeb_id}/bookings/{booking_id}")
def update_celeb_booking(celeb_id: str, booking_id: str, payload: BookingStatus, get_agent_response=Depends(verify_agent_access_token)):
    """ an endpoint to update the status of a booking
    Args:
        celeb_id: the celebrity id
        booking_id: the booking to be affected
        payload: the new update
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump(), 205)
    
    booking_response = storage.get_booking(booking_id, celeb_id=celeb_id)
    if not booking_response.status:
        content = api_response(False, "This booking is not found for the celeb")
        return JSONResponse(content.model_dump)
    
    if payload.status != Status.APPROVED and payload.status != Status.CANCELLED:
        content = api_response(False, "The agent can only approve or cancel bookings")
        return JSONResponse(content.model_dump())
    
    booking = booking_response.payload
    booking.status = payload.status
    booking.save()

    content = api_response(True, "Booking info has been updated successfully", booking.to_dict())
    return JSONResponse(content.model_dump())
