from fastapi import Request
import jwt
from dotenv import load_dotenv
import os
from src.database.mongo import get_db

load_dotenv()

def session(req: Request):
    token = req.cookies.get("sessionToken")
    if not token:
        return {"pubkey": None, "balance": 0}
    try:
        secret = os.environ.get("JWT_SECRET")
        if secret is None:
            raise RuntimeError("JWT_SECRET is not set.")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return {"pubkey": payload["pubkey"], "balance": get_db()["users"].find_one({ "pubkey": payload["pubkey"] })}
    except:
        return {"pubkey": None, "balance": 0}