import os
import lightspark
from datetime import datetime, timezone
import httpx
from src.database.mongo import get_db
from src.database.redis import redis

OFFERS = [
    {
        "id": "3492623f-528d-4cec-80d9-a8e6b8f9dec8",
        "title": "1000 Credit Package",
        "description": "Purchase 1000 credits for API access.",
        "amount": 50,
        "currency": "USD",
        "type": "top-up",
        "payment_method": "lightning"
    },
    {
        "id": "b2ba7eae-bf07-4128-8f65-514149abe2e4",
        "title": "1000 Credit Package",
        "description": "Purchase 10000 credits for API access.",
        "amount": 450,
        "currency": "USD",
        "type": "top-up",
        "payment_method": "lightning"
    },
    {
        "id": "3492623f-528d-4cec-80d9-a8e6b8f9dec8",
        "title": "1000 Credit Package",
        "description": "Purchase 100000 credits for API access.",
        "amount": 3500,
        "currency": "USD",
        "type": "top-up",
        "payment_method": "lightning"
    }
]

def create_response(authorization_token: str):
    return {
        "version": "0.1.0",
        "offers": OFFERS,
        "payment_request_url": "http://localhost:8000/user/payment",
        "authorization_token": authorization_token,
        "terms_url": "http://localhost:3000/terms"
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

async def create_lightning_invoice(user_id, offer, expiry):    

    ls_client_id = os.getenv("LIGHTSPARK_ID")
    ls_secret = os.getenv("LIGHTSPARK_SECRET")
    ls_node_id = os.getenv("LIGHTSPARK_NODE")

    if not ls_client_id or not ls_secret or not ls_node_id:
        raise RuntimeError("Lightspark env variables not set.")

    client = lightspark.LightsparkSyncClient(
        api_token_client_id=ls_client_id,
        api_token_client_secret=ls_secret,
    )

    amount_msats = (await get_usd_amount_in_sats(offer["amount"])) * 1000
    expiry_secs = int((expiry - datetime.now(timezone.utc)).total_seconds())
    invoice = client.create_invoice(
        node_id=ls_node_id,
        amount_msats=amount_msats,
        memo=offer["title"],
        expiry_secs=expiry_secs
    )
    payments = get_db()["payments"]
    await payments.insert_one({
        "invoice_id": invoice.id,
        "user_id": user_id,
        "offer_id": offer["id"],
        "completed": False
    })

    return invoice.data.encoded_payment_request