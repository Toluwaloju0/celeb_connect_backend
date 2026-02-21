from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import getenv
from database.storage_engine import DBStorage

DATABASE_URL = (
    f"mysql+mysqldb://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}"
    f"@{getenv('DB_HOST')}:{getenv('DB_PORT')}/{getenv('DB_NAME')}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # IMPORTANT for MySQL
    pool_recycle=1800
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