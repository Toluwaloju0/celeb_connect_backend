""" a module to define how responses would be for my endpoints and functions"""

from typing import Dict
from pydantic import BaseModel

class APIResponse(BaseModel):
    """ the response type for my all my endpoints """

    status: bool
    message: str
    data: Dict | None


class FunctionResponse(BaseModel):
    """ the response type for all my functions """

    status: bool
    payload: Dict | None
