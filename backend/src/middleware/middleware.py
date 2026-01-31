from fastapi import Request, WebSocket
from typing import Union
import jwt
from dotenv import load_dotenv
import os
from src.database.mongo import get_db
import time

load_dotenv()

async def creator_session(request: Request):
    token = request.cookies.get("jwt")
    print(token)
    if not token:
        return None
    try:
        secret = os.environ.get("JWT_SECRET")
        if secret is None:
            raise RuntimeError("JWT_SECRET is not set.")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        if payload["iss"] != "btc-mcp" or payload["exp"] < time.time():
            return None
        creator = await get_db()["creators"].find_one({"pubkey": payload["pubkey"]})
        return {"pubkey": payload["pubkey"], "credits": creator["credits"] if creator else 0}
    except:
        return None
    
async def user_session(request: Union[Request, WebSocket]):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith('Bearer '):
        return None
    user_id = auth.split(' ')[1]
    users = get_db()["users"]
    user = await users.find_one({ "user_id": user_id })
    if user == None:
        return None
    else:
        return { "user_id": user["user_id"], "balance": user["balance"] }