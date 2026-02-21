""" a module to delete a refresh token from the database"""

from database.storage_engine import DBStorage

def delete_refresh_token(token, storage: DBStorage):
    """ a function to delete the provided token from the database if found
    Args:
        token: the token to be deleted
        storage: the session and storage object to delete the token
    """

    refresh_object_response = storage.get_refresh_token(token)
    if refresh_object_response.status:
        refresh_object_response.payload.delete(storage)
