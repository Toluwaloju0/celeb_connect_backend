""" the main application module """

from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from routes.auth_route import auth
from routes.user_route import user
from routes.admin_route import admin
from routes.agent_route import agent
from database.storage_engine import DBStorage
from middlewares.session_middleware import DBSessionMiddleware, SessionLocal
from utils.create_admin import create_admin
from utils.create_all_tables import create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create application tables and the configured bootstrap administrator."""
    create_tables()
    session = SessionLocal()
    try:
        create_admin(DBStorage(session))
    finally:
        session.close()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite (React)
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],  # Authorization, Content-Type, etc
)


@app.get("/", response_class=HTMLResponse)
def welcome_page():
    """Return a simple welcome page for the API."""

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Celeb Connect API</title>
    </head>
    <body>
        <main>
            <h1>Welcome to the Celeb Connect API</h1>
            <p>Your connection to celebrity bookings and account services is ready.</p>
        </main>
    </body>
    </html>
    """

@app.get("/status")
def status():
    """ a function to display the status of the api"""

    return {"Message": "API is working correctly"}


app.include_router(auth)
app.include_router(user)
app.include_router(admin)
app.include_router(agent)

app.add_middleware(DBSessionMiddleware)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)
