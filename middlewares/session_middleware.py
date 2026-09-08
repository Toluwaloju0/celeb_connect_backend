from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from os import getenv
from database.storage_engine import DBStorage

database_settings = {
    "DB_HOST": getenv("DB_HOST"),
    "DB_PORT": getenv("DB_PORT"),
    "DB_NAME": getenv("DB_NAME"),
    "DB_USER": getenv("DB_USER"),
    "DB_PASSWORD": getenv("DB_PASSWORD"),
}
missing_settings = [name for name, value in database_settings.items() if not value]
if missing_settings:
    raise RuntimeError(
        f"Missing database environment variables: {', '.join(missing_settings)}"
    )

try:
    database_port = int(database_settings["DB_PORT"])
except ValueError as error:
    raise RuntimeError("DB_PORT must be a valid port number") from error

DATABASE_URL = URL.create(
    "postgresql+psycopg",
    username=database_settings["DB_USER"],
    password=database_settings["DB_PASSWORD"],
    host=database_settings["DB_HOST"],
    port=database_port,
    database=database_settings["DB_NAME"],
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"sslmode": "require"},
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # create db session
        session = SessionLocal()

        try:
            # attach to request state
            request.state.storage = DBStorage(session)
            response = await call_next(request)
            return response
        finally:
            session.close()
