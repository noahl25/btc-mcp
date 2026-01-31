from fastapi import APIRouter, Body
from src.database.mongo import get_db
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

user = APIRouter()

async def create_user():
    id = str(uuid4())
    users = get_db()["users"]
    await users.insert_one({ "user_id": id, "balance": 0 })
    return id

@user.post("/user-signin")
async def me():
    return { "id": await create_user() }

@user.post("/payment")
async def payment(offer_id: str = Body(...)):
    pass