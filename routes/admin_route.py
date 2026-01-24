""" a module to define the admin routes and operations in the database """

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from database.storage_engine import storage
from models.agent_model import AgentCreate, Agent
from models.admin_model import Admin
from utils.responses import api_response
from utils.check_email import check_email
from utils.check_password import ph
from middlewares.admin_access_token import get_admin_from_access_token
from services.email_sender import email_sender


admin = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(get_admin_from_access_token)])

@admin.post("/agent/add")
def add_agent(agent: AgentCreate, get_agent_response = Depends(get_admin_from_access_token)):
    """ an endpoint to create a new agent by the admin
    Args:
        agent: the agent informations holding the agent name, email and password
        get_agent_response = the admin as saved in the access token
    """

    if not get_agent_response.status:
        content = api_response(False, "The user is not allowed to use this route")
        return JSONResponse(content.model_dump())
    
    if not get_agent_response.payload:
        content = api_response(False, "The access token is expired refresh to user the application")
        return JSONResponse(content.model_dump())

    admin: Admin = get_agent_response.payload

    # check if the agent exists in the database already
    saved_agent_response = storage.get_admin_from_email(agent.email)
    if saved_agent_response.status:
        content = api_response(False, "An agent with this email address exists")
        return JSONResponse(content.model_dump())

    check_email_response = check_email(agent.email)
    if not check_email_response.status:
        content = api_response(False, "The email domain is not approved by our servers")
        return JSONResponse(content.model_dump())
    
    # send an email to the agent with an otp code for email verification
    password_response = email_sender.send_agent_password(agent.email)
    password = password_response.payload

    admin.agents.append(Agent(agent.name, agent.email, ph.hash(password), agent.phone_number))
    admin.save()

    content = api_response(True, f"Agent {agent.name} has been added successfully")
    return JSONResponse(content.model_dump())

@admin.patch("/agent/{agent_id}/update")
def update_agent(agent_id: str, get_admin_response = Depends(get_admin_from_access_token)):
    """ an endpoint to update an agent """

    pass