from fastapi import APIRouter, Response, Request, Depends
import secrets
import jwt
from lnurl import url_encode
from src.database.redis import redis
from src.database.mongo import get_db
from coincurve import PublicKey
import hashlib
import time
from dotenv import load_dotenv
import os
from src.middleware.middleware import creator_session

creator = APIRouter()

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

@creator.get("/creator-signin")
async def auth(request: Request):
    k1 = secrets.token_hex(32)
    await redis.set(f"lnurl-k1-{k1}", "pending", 300)
    callback = f"{str(request.base_url).rstrip("/")}/lnurl-auth/callback?k1={k1}"
    return { "lnurl": url_encode(callback), "k1": k1 }

@creator.get("/creator-callback")
async def callback(k1: str, key: str, sig: str):
    challenge = await redis.get(f"lnurl-k1-{k1}") 
    if not challenge:
        return { "status": "error", "message": "Unkown challenge." }
    if not verify_signature(key, k1, sig):
        return { "status": "error", "message": "Invalid signature." }
    
    await redis.set(f"lnurl-k1-{k1}", f"auth:{key}", ex=300)
    
    return { "status": "success" }

@creator.get("/creator-signin/{k1}")
async def check_session(k1: str, response: Response):
    state = await redis.get(f"lnurl-k1-{k1}")
    
    if state and state.startswith("auth:"):
        pubkey = state.split(":")[1]
        
        creators = get_db()["creators"]
        await creators.update_one({"pubkey": pubkey}, {"$setOnInsert": {"credits": 0}}, upsert=True)

        token = create_session(pubkey)
        response.set_cookie(
            key="jwt",
            value=token,
            httponly=True,
            secure=os.getenv("ENV") != "development",
            samesite="lax"
        )
        
        await redis.delete(f"lnurl-k1-{k1}")
        return { "status": "success" }
    if not state:
        return { "status": "Invalid k1" }
    return { "status": "pending" }
    
@creator.get("/session")
async def session(session = Depends(creator_session)):
    if not session:
        return { "authenticated": False }
    return { "authenticated": True }