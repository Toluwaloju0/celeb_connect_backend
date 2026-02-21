""" a module to get the user from the access token provided for the agents """

from fastapi import Request

from utils.cookie_token import token_manager

def verify_agent_access_token(request: Request):
    """ a function to validate the agent access token to ensure that an agent is the one querying the endpoints """

    access_token = request.cookies.get("access_token")

    get_agent_response = token_manager.verify_agent_access_token(access_token, request.state.storage)

    return get_agent_response