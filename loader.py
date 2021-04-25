from fastapi import FastAPI, APIRouter

from config import DB_URL, DB_NAME, DB_USERS_COLLECTION_NAME
from db import Database

auth_router = APIRouter(prefix="/auth", tags=["auth"])
bots_router = APIRouter(prefix="/bots", tags=["bots"])
db = Database()
app = FastAPI(title="Bot management service")


@app.on_event("startup")
async def setup_db_connection():
    await db.connect(db_url=DB_URL,
                     db_name=DB_NAME,
                     users_collection_name=DB_USERS_COLLECTION_NAME)


@app.get("/", response_model=dict[str, str], description="Test endpoint. Returns hello world message")
async def root():
    return {"message": "Hello World"}
