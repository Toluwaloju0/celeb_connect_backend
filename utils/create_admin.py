"""Create the configured administrator account when the application starts."""

from os import getenv

from database.storage_engine import DBStorage
from models.admin_model import Admin
from utils.check_password import ph


def create_admin(storage: DBStorage):
    """Create the environment-configured administrator when none exists."""
    settings = {
        "ADMIN_NAME": getenv("ADMIN_NAME"),
        "ADMIN_EMAIL": getenv("ADMIN_EMAIL"),
        "ADMIN_PASSWORD": getenv("ADMIN_PASSWORD"),
    }
    missing_settings = [name for name, value in settings.items() if not value]
    if missing_settings:
        raise RuntimeError(
            f"Missing admin environment variables: {', '.join(missing_settings)}"
        )

    if storage.get_admin_count() >= 1:
        return False

    admin = Admin()
    admin.name = settings["ADMIN_NAME"]
    admin.email = settings["ADMIN_EMAIL"]
    admin.password = ph.hash(settings["ADMIN_PASSWORD"])
    admin.save(storage)
    return True
