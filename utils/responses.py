""" a module to define functions to call responses for the endpoints and functions """

from typing import Dict

from models.responses import FunctionResponse, APIResponse

def function_response(status: bool, payload: Dict | None = None):
    """ a  function to call the function response class """

    return FunctionResponse(status=status, payload=payload)


def api_response(status: bool, message: str, data: Dict | None = None):
    """ a function to call the api response class """

    return APIResponse(status=status,message=message, data=data)
