from fastapi import APIRouter, Response
import secrets
import jwt
from lnurl import Lnurl
from src.database.redis import redis
from src.database.mongo import get_db
from coincurve import PublicKey
import hashlib
import time
from dotenv import load_dotenv
import os

lnauth = APIRouter()

load_dotenv()

def create_session(pubkey: str):
    payload = {
        "pubkey": pubkey,
        "iat": int(time.time()),
        "exp": int(time.time()) + 7 * 24 * 3600,
        "iss": "btc-mcp"
    }
    secret = os.environ.get("JWT_SECRET")
    if secret is None:
        raise RuntimeError("JWT_SECRET is not set.")
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token

def verify_signature(pubkey_hex: str, k1: str, sig_hex: str):
    try:
        pubkey = PublicKey(bytes.fromhex(pubkey_hex))
        msg = hashlib.sha256(bytes.fromhex(k1)).digest()
        return pubkey.verify(bytes.fromhex(sig_hex), msg)
    except Exception:
        return False

@lnauth.get("/auth")
async def auth():
    k1 = secrets.token_hex(32)
    await redis.set(f"lnurl-k1-{k1}", "pending", 3600)
    callback = f"http://localhost:8000/lnurl-auth/callback?k1={k1}"
    return { "lnurl": Lnurl(callback).bech32, "k1": k1 }

@lnauth.get("/lnurl-callback")
async def callback(k1: str, key: str, sig: str, response: Response):
    challenge = await redis.get(f"lnurl-k1-{k1}")
    if not challenge:
        return { "status": "error", "message": "Unkown challenge." }
    if not verify_signature(key, k1, sig):
        return { "status": "error", "message": "Invalid signature." }
    
    users = get_db()["users"]
    await users.update_one(
        {"pubkey": key},
        {"$setOnInsert": {"balance": 0}},
        upsert=True
    )
    
    await redis.delete(f"lnurl-k1-{k1}")

    token = create_session(key)
    response.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        secure=os.getenv("ENV") == "development",
        samesite="lax",
        max_age=7 * 24 * 3600
    )
    return {"status": "success" }

    
