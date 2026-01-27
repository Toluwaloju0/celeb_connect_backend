""" a module to create a file management class for managing  all file activities """

import os
import shutil

from fastapi import UploadFile

from utils.id_string import uuid
from utils.responses import function_response

class FileManager:
    """ the file management class """

    def __init__(self):
        """The class initilializer"""

        self.agent_path = "/tmp/celeb_connect/agents"
        self.user_path = "/tmp/celeb_connect/users"
        self.admin_path = "/tmp/celeb_connect/admin"

        os.makedirs(self.agent_path, exist_ok=True)
        os.makedirs(self.user_path, exist_ok=True)
        os.makedirs(self.admin_path, exist_ok=True)

    def save_celeb_file(self, file: UploadFile):
        """ a method to save the file to the server
        Args:
            file: the file to be saved
        """

        ext = file.filename.split(".")[-1]
        location = f"{uuid()}.{ext}"

        try:
            with open(f"{self.agent_path}/{location}", "wb") as profile_file:
                shutil.copyfileobj(file.file, profile_file)
            return function_response(True, location)
        except Exception:
            return function_response(False)
        finally:
            file.file.close()

    def delete_celeb_file(self, file_url):
        """ a method to delete a celebrity profile image
        Args:
            file_url (str): the file location
        """

        file_path = f"{self.agent_path}/{file_url}"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{file_path}' deleted.")
        else:
            print(f"The file '{file_path}' does not exist.")

    def save_agent_file(self, file: UploadFile):
        """ a method to save the file to the server
        Args:
            file: the file to be saved
        """

        ext = file.filename.split(".")[-1]
        location = f"{uuid()}.{ext}"

        try:
            with open(f"{self.admin_path}/{location}", "wb") as profile_file:
                shutil.copyfileobj(file.file, profile_file)
            return function_response(True, location)
        except Exception:
            return function_response(False)
        finally:
            file.file.close()

    def delete_agent_file(self, file_url):
        """ a method to delete a celebrity profile image
        Args:
            file_url (str): the file location
        """

        file_path = f"{self.admin_path}/{file_url}"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{file_path}' deleted.")
        else:
            print(f"The file '{file_path}' does not exist.")
    

file_manager = FileManager()