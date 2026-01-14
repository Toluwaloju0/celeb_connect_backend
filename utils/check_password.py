""" a module to check the strength of the password of the user"""

import string
from argon2 import PasswordHasher

from .responses import function_response

ph = PasswordHasher(salt_len=50, hash_len=10)

def check_password_strength(password: str):
    """ a function to check the strength of the user password
    Args:
        password (str): the password to be checked
    """

    if len(password) < 8:
        return function_response(False)
    
    has_upper, has_lower = False, False
    has_symbol, has_number = False, False

    for char in password:
        if char.isalpha() and char.islower():
            has_lower = True
        if char.isalpha() and char.isupper():
            has_upper = True
        elif char.isdigit():
            has_number = True
        elif char in string.punctuation:
            has_symbol = True
    
    return function_response(has_upper and has_lower and has_number and has_symbol)
