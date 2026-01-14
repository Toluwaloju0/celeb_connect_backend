""" the main application module """

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes.auth_route import auth

app = FastAPI()

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


@app.get("/")
def welcome_page():
    """ a function to welcome users into the application """

    return "Welcome to the Celeb Connect API"

@app.get("/status")
def status():
    """ a function to display the status of the api"""

    return {"Message": "API is working correctly"}


app.include_router(auth)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)