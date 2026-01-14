""" a module to create the base class for all server """

from datetime import datetime
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from utils.id_string import uuid

class Base(DeclarativeBase):
    """ the base class which provides all the database related tables"""
    pass


class Basemodel:
    """ the base model class for all the database connection equal properties """

    id: Mapped[str] = mapped_column(String(60), primary_key=True, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    def __init__(self):
        """The class initializer"""

        self.id = uuid()
        self.created_at = datetime.now()

    def to_dict(self):
        """ a method to get the dictionary representation of the class"""

        my_dict = {}
        my_dict.update(self.__dict__)
        if my_dict.get("password"):
            del my_dict["password"]
        if my_dict.get("_sa_instance_state"):
            del my_dict["_sa_instance_state"]
        if my_dict.get("created_at"):
            my_dict["created_at"] = str(my_dict["created_at"])
        if my_dict.get("date_of_birth"):
            my_dict["date_of_birth"] = str(my_dict["date_of_birth"])

        return my_dict

    def save(self):
        """A method to save the class to the database"""

        from database.storage_engine import storage

        storage.save(self)
        return "saved"
    
    def __str__(self):
        """ a function to use when printing the class"""

        return f"{self.to_dict()}"