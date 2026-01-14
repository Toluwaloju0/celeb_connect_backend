""" a module to check the user email address if its in a valid format """

from .responses import function_response

def check_email(email: str):
    """ a function to check the email of given if it has a valid domain
    Args:
        email (str): the email to be checked
    """

    domain = email.split("@")[1]

    if not domain or domain not in ["gmail.com", "yahoo.com"]:
        return function_response(False)
    return function_response(True)
