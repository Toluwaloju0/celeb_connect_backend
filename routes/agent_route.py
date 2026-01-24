""" a module to define the agent route """

from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Body
from fastapi.responses import JSONResponse
from typing import Dict, Optional

from models.agent_model import Agent
from models.celebrity_model import CelebCreate, Celeb
from middlewares.agent_access_token import verify_agent_access_token
from utils.responses import api_response
from utils.check_password import ph, check_password_strength

agent = APIRouter(prefix="/agent", tags=["Agents"], dependencies=[Depends(verify_agent_access_token)])

@agent.patch("/password")
def update_password(payload: Dict[str, str] = Body(), get_agent_response = Depends(verify_agent_access_token)):
    """ an endpoint to get a new agent password and update the agent password
    This would also verify the agents email address
    
    Args:
        payload: the request body
        get_agent_response: the agent from the access token
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump())
    
    if not get_agent_response.payload:
        cotent = api_response(False, "The access token has expired, refresh and try again")
        return JSONResponse(content.model_dump())
    agent = get_agent_response.payload
    
    old_password, new_password = payload.get("old_password"), payload.get("new_password")
    if not old_password or not new_password or old_password == new_password:
        content = api_response(False, "Both the old and the new password must be provided and must be different")
        return JSONResponse(content.model_dump())
    
    try:
        ph.verify(agent.password, old_password)
    except VerifyMismatchError:
        content = api_response(False, "The old password does not match the new one")
        return JSONResponse(cotent.model_dump())
    
    password_strength_checker = check_password_strength(new_password)
    if not password_strength_checker.status:
        content = api_response(False, "The provided password is not up to the required strength")
        return JSONResponse(content.model_dump())
    
    agent.password = ph.hash(new_password)
    agent.email_verified = True
    agent.save

    content = api_response(True, "Password update successful", agent.to_dict())
    return JSONResponse(content.model_dump())

@agent.post("/celeb/add")
def add_celebrity(celeb: CelebCreate, get_agent_response = Depends(verify_agent_access_token)):
    """ an endpoint to add a new celeb to the database for this agent """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to visit this route")
        return JSONResponse(content.model_dump())
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump())
    
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
        return JSONResponse(content.model_dump())
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired, Refresh and try again")
        return JSONResponse(content.model_dump())
    
    agent: Agent = get_agent_response.payload

    # get the celebrities from the database using the required offset and limit
    
