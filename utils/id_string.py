""" a module to create a function which creates a uuid v4 string"""

from uuid import uuid4

def uuid() -> str:
    """ a function to create a uuid v4 string """

    return str(uuid4())
