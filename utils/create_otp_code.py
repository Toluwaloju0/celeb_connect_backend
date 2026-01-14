""" a module to define a function which creates an otp code"""

from uuid import uuid4

def create_otp():
    """ the functon to create an otp code for a user
    Return: the otp code to be used
    """

    return str(uuid4())[2:8]
