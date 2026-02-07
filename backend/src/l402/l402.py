import os
import lightspark
from datetime import datetime, timezone
import httpx
from src.database.mongo import get_db
from src.database.redis import redis
from dotenv import load_dotenv
import secrets

load_dotenv()

OFFERS = [
    {
        "id": "3492623f-528d-4cec-80d9-a8e6b8f9dec8",
        "title": "1000 Credit Package",
        "description": "Purchase 1000 credits for API access.",
        "amount": 50,
        "currency": "USD",
        "type": "top-up",
        "payment_method": "lightning",
        "balance": 1000
    },
    {
        "id": "b2ba7eae-bf07-4128-8f65-514149abe2e4",
        "title": "10000 Credit Package",
        "description": "Purchase 10000 credits for API access.",
        "amount": 450,
        "currency": "USD",
        "type": "top-up",
        "payment_method": "lightning",
        "balance": 10000
    },
    {
        "id": "3497623f-558d-4cec-80d9-48e6bdf9dec8",
        "title": "100000 Credit Package",
        "description": "Purchase 100000 credits for API access.",
        "amount": 3500,
        "currency": "USD",
        "type": "top-up",
        "payment_method": "lightning",
        "balance": 100000
    },
    {
        "id": "b5bc8ce8-a93e-4ef2-991a-d7c0700af962",
        "title": "Stake 100 credits",
        "description": "Stake 100 credits to your specified MCP server.",
        "amount": 5,
        "currency": "USD",
        "type": "stake",
        "payment_method": "lightning",
        "balance": 100
    },
        {
        "id": "b5bc82e8-a93e-4ef2-9914-d7c3750af962",
        "title": "Stake 1000 credits",
        "description": "Stake 1000 credits to your specified MCP server.",
        "amount": 50,
        "currency": "USD",
        "type": "stake",
        "payment_method": "lightning",
        "balance": 1000
    },
    {
        "id": "8fd9b383-0325-4461-bf35-45a278bbc025",
        "title": "Stake 10000 credits",
        "description": "Stake 10000 credits to your specified MCP server.",
        "amount": 500,
        "currency": "USD",
        "type": "stake",
        "payment_method": "lightning",
        "balance": 10000
    }

]

def get_offer_by_id(offer_id: str):
    for offer in OFFERS:
        if offer["id"] == offer_id:
            return offer
    return None

def create_response(authorization_token: str, type: str, description: str = ""):
    return {
        "version": "0.1.0",
        "offers": [offer for offer in OFFERS if offer["type"] == type],
        "payment_request_url": f"http://localhost:8000/api/payments/{type}",
        "authorization_token": authorization_token,
        "terms_url": "http://localhost:3000/terms",
        "description": description
    }

async def get_usd_amount_in_sats(cents: int):
    cached = await redis.get("btc:sats_per_cent")
    if cached:
        return int(float(cached) * cents)

    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get("https://api.kraken.com/0/public/Ticker?pair=BTCUSD")
        r.raise_for_status()
        btc_price = float(r.json()["result"]["XXBTZUSD"]["c"][0])

    sats_per_cent = 100_000_000 * 0.01 / btc_price
    await redis.setex("btc:sats_per_cent", 600, sats_per_cent)
    return int(sats_per_cent * cents)

async def create_lightning_invoice(user_id, offer, expiry, agent_id=None):    

    ls_client_id = os.getenv("LIGHTSPARK_ID")
    ls_secret = os.getenv("LIGHTSPARK_SECRET")
    ls_node_id = os.getenv("LIGHTSPARK_NODE")

    if not ls_client_id or not ls_secret or not ls_node_id:
        raise RuntimeError("Lightspark env variables not set.")

    client = lightspark.LightsparkSyncClient(
        api_token_client_id=ls_client_id,
        api_token_client_secret=ls_secret,
    )

    offer = get_offer_by_id(offer)
    if not offer:
        return None
    amount_msats = (await get_usd_amount_in_sats(offer["amount"])) * 1000
    expiry_secs = int((expiry - datetime.now(timezone.utc)).total_seconds())
    invoice = client.create_test_mode_invoice(
        local_node_id=ls_node_id,
        amount_msats=amount_msats,
        memo=offer["title"]
    )
    payments = get_db()["payments"]
    payment_record = {
        "invoice_id": invoice,
        "user_id": user_id,
        "offer_id": offer["id"],
        "completed": False
    }
    if agent_id:
        payment_record["agent_id"] = agent_id
    await payments.insert_one(payment_record)

    return invoice