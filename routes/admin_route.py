""" a module to define the admin routes and operations in the database """

from fastapi import APIRouter, Depends, Body, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict

from database.storage_engine import storage
from models.agent_model import AgentCreate, Agent, UpdateAgentTier
from models.admin_model import Admin
from models.user import UpdateUserLevel
from utils.responses import api_response
from utils.check_email import check_email
from utils.check_password import ph
from middlewares.admin_access_token import get_admin_from_access_token
from services.email_sender import email_sender
from services.file_management import file_manager


admin = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_from_access_token)])

@admin.post("/agent/add")
def add_agent(agent: AgentCreate, get_admin_response = Depends(get_admin_from_access_token)):
    """ an endpoint to create a new agent by the admin
    Args:
        agent: the agent informations holding the agent name, email and password
        get_admin_response
e = the admin as saved in the access token
    """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)

    admin: Admin = get_admin_response.payload

    # check if the agent exists in the database already
    saved_agent_response = storage.get_agent_from_email(agent.email)
    if saved_agent_response.status:
        content = api_response(False, "An agent with this email address exists")
        return JSONResponse(content.model_dump(), 500)

    check_email_response = check_email(agent.email)
    if not check_email_response.status:
        content = api_response(False, "The email domain is not approved by our servers")
        return JSONResponse(content.model_dump(), 500)
    
    # send an email to the agent with an otp code for email verification
    password_response = email_sender.send_agent_password(agent.email)
    password = password_response.payload

    admin.agents.append(Agent(agent.name, agent.email, ph.hash(password), agent.phone_number))
    admin.save()

    content = api_response(True, f"Agent {agent.name} has been added successfully")
    return JSONResponse(content.model_dump())

@admin.get("/agents")
@admin.get("/agents/{agent_id}")
def get_agent_info(agent_id: str | None = None, page: int = 1, offset: int=10, limit: int=10, get_admin_response=Depends(get_admin_from_access_token)):
    """ an endpoint to get all or one of an agent if the agent_id is provided
    Args:
        agent_id: the agent id if it is provided
        get_admin_response: the admin response from the access token
    """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)
    
    if agent_id:
        agent_response = storage.get_agent_from_id(agent_id)
        agent = agent_response.payload
        content = api_response(True, "Agent gotten successfuly", agent.to_dict()) if agent_response.status else api_response(False, "no agent is gotten for the provided id")
        return JSONResponse(content.model_dump())
    
    page = page - 1 if page >= 1 else 0
    
    agents_response = storage.get_agents(offset * page, limit)
    content = api_response(True, "Agents gotten successfully", agents_response.payload) if agents_response.status else api_response(False, "No agent is found for the provided page")
    return JSONResponse(content.model_dump())

@admin.delete("/agent/{agent_id}")
def delete_admin(agent_id: str, get_admin_response = Depends(get_admin_from_access_token)):
    """an endpoint to delete an agent from the database along with all the agents celebs
    Args:
        agent_id: the id of the agent to be added
        get_admin_response: the admin response from the access token
        """
    
    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)
    
    admin = get_admin_response.payload
    
    agent_response = storage.get_agent_from_id(agent_id)
    if not agent_response.status:
        content = api_response(False, "No agent is found")
        return JSONResponse(content.model_dump())
    # delete the agent
    agent = agent_response.payload
    if agent.profile_url:
        file_manager.delete_agent_file(agent.profile_url)
    agent.delete()
    content = api_response(True, "Agent deleted")
    return JSONResponse(content.model_dump())

@admin.patch("/agent/{agent_id}/profile/update")
def update_agent(agent_id: str, payload: Dict[str, str] = Body(), get_admin_response = Depends(get_admin_from_access_token)):
    """ an endpoint to update an agent """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)
    
    name = payload.get("name")
    if not name:
        content = api_response(False, "Only the name can be updated")
        return JSONResponse(content.model_dump())

    agent_response = storage.get_agent_from_id(agent_id)
    if not agent_response.status:
        content = api_response(False, "No agent is found with the provided id")
        return JSONResponse(content.model_dump())
    
    agent = agent_response.payload
    if agent.name == name:
        content = api_response(False, "No update to save")
        return JSONResponse(content.model_dump())

    agent.name = name
    agent.save()

    content = api_response(True, "the agent has been updated successfully", agent.to_dict())
    return JSONResponse(content.model_dump())

@admin.put("/agent/{agent_id}/profile/picture")
def add_agent_image(agent_id: str, file: UploadFile = File(), get_admin_response = Depends(get_admin_from_access_token)):
    """
    Docstring for add_agent_image
    
    :param agent_id: the agent id for the agent
    :type agent_id: str
    :param file: the picture file
    :type file: UploadFile
    :param get_admin_response: the admin response from the access token
    """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)
    
    file_type = file.filename.split(".")[-1]

    if not file_type or file_type not in ["png", "jpeg"]:
        content = api_response(False, "The provided file is not in the required format\n\nWe only accept .png or .jpeg files")
        return JSONResponse(content.model_dump(), 500)
    
    agent_response = storage.get_agent_from_id(agent_id)
    if not agent_response.status:
        content = api_response(False, "No agent is found for the provided agent id")
        return JSONResponse(content.model_dump(), 500)
    
    agent: Agent = agent_response.payload

    location_response = file_manager.save_agent_file(file)
    if not location_response.status:
        content = api_response(False, "The file was not successfully saved")
        return JSONResponse(content.model_dump(), 500)
    
    if agent.profile_url:
        file_manager.delete_agent_file(agent.profile_url)

    agent.profile_url = location_response.payload
    agent.save()
    content = api_response(True, "The image has been saved successfully", agent.to_dict())
    return JSONResponse(content.model_dump())

@admin.patch("/agent/{agent_id}/profile/level")
def update_agent_tier(agent_id: str, payload: UpdateAgentTier, get_admin_response = Depends(get_admin_from_access_token)):
    """an endpoint to update the tier of an agent by an admin
    Args:
        agent_id: the id of the agent
        payload: the new tier of the agent
        get_admin_response: the admin response from the access token
    """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)
    
    agent_response = storage.get_agent_from_id(agent_id)
    if not agent_response.status:
        content = api_response(False, "No agent is found for the provided id")
        return JSONResponse(content.model_dump(), 500)

    new_tier = payload.tier
    if not new_tier:
        content = api_response(False, "The agent tier is not provided")
        return JSONResponse(content.model_dump(), 500)
    
    agent: Agent = agent_response.payload
    agent.tier = new_tier
    agent.save()
    content = api_response(True, "Agent tier updated successfully", agent.to_dict())
    return JSONResponse(content.model_dump())

@admin.get("/celebs")
def get_all_celebs(page: int = 1, limit: int = 10, get_admin_response = Depends(get_admin_from_access_token)):
    """ a method to get the admin response for the provided page
    Args:
        page: the current page
        limit: the amount of data to be presented for each page
    """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)
    
    page = 0 if page - 1 < 0 else page - 1

    celebs_response = storage.get_celebrities_for_admin(limit, page * limit)
    content = api_response(True, "Celebrities gotten", celebs_response.payload) if celebs_response.status else api_response(False, "No celebrity found")
    return JSONResponse(content.model_dump())

@admin.get("/users")
@admin.get("/users/{user_id}")
def get_all_user(user_id: str = None, page: int = 1, limit: int = 10, get_admin_response = Depends(get_admin_from_access_token)):
    """ an endpoint to get the user from the database for the admin
    Args:
        user_id: the user id of the user
        page: the current page
        limit: the limit of the page
    """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump(), 205)
    
    page = 0 if page - 1 > 0 else page - 1
    
    if not user_id:
        user_response = storage.get_users_for_admin(limit, limit * page)

        content = api_response(True, "Users retrieved", user_response.payload) if user_response.status else api_response(False, "No user is found")
        return JSONResponse(content.model_dump())
    
    user_response = storage.get_user_by_id(user_id)
    content = api_response(True, "User gotten", user_response.payload.to_dict()) if user_response.status else api_response(False, "No user with this id found")
    return JSONResponse(content.model_dump())

@admin.delete("/user/{user_id}")
def delete_user_by_admin(user_id: str, get_admin_response = Depends(get_admin_from_access_token)):
    """an endpoint to delete a user by an admin
    Args:
        user_id: the id of the user to be deleted
    """

    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to use the application")
        return JSONResponse(content.model_dump(), 205)
    
    user_response = storage.get_user_by_id(user_id)
    if not user_response.status:
        content = api_response(False, "No user found")
        return JSONResponse(content.model_dump(), 500)
    
    user = user_response.payload
    user.delete()

    content = api_response(True, "The user has been deleted successfully")
    return JSONResponse(content.model_dump())

@admin.patch("/user/{user_id}/profile/level")
def update_user_level(user_id: str, payload: UpdateUserLevel, get_admin_response = Depends(get_admin_from_access_token)):
    """ an endpoint for an admin to update a user level to either basic or premium
    Args:
        user_id: the id of the user to be updated
        payload: the user level to be updated
        get_admin_response: the admin response from the access token
    """
    if not get_admin_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump(), 401)
    
    if not get_admin_response.payload:
        content = api_response(False, "The access token is expired refresh to use the application")
        return JSONResponse(content.model_dump(), 205)
    
    user_response = storage.get_user_by_id(user_id)
    if not user_response.status:
        content = api_response(False, "No user is found for the provided id")
        return JSONResponse(content.model_dump(), 500)
    
    user_level = payload.new_level
    user = user_response.payload

    user.level = user_level
    user.old_level = user_level

    user.save()
    content = api_response(True, "The users level has been updated successfully", user.to_dict())
    return JSONResponse(content.model_dump())
