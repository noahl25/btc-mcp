from fastapi import APIRouter, Body, Request, HTTPException
from fastapi.responses import JSONResponse
from src.database.mongo import get_db
from uuid import uuid4
from dotenv import load_dotenv
from src.l402.l402 import create_lightning_invoice, get_offer_by_id
from datetime import datetime, timezone, timedelta
import lightspark
import os

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
async def payment(offer_id: str = Body(...), authorization_token: str = Body(...)):
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=5)
    invoice = await create_lightning_invoice(authorization_token, offer_id, expiry)
    if not invoice:
        raise HTTPException(400, "Invalid offer id.")
    return invoice

@user.post("/webhook/lightspark")
async def lightspark_webhook(request: Request): 

    sig = request.headers.get(lightspark.SIGNATURE_HEADER)
    webhook_signing_key = os.getenv("LIGHTSPARK_WEBHOOK_SIGN")
    if not sig or not webhook_signing_key:
        return JSONResponse({}, 200)
    
    ls_client_id = os.getenv("LIGHTSPARK_ID")
    ls_secret = os.getenv("LIGHTSPARK_SECRET")
    ls_node_id = os.getenv("LIGHTSPARK_NODE")

    if not ls_client_id or not ls_secret or not ls_node_id:
        return JSONResponse({}, 200)

    try:
        event = lightspark.WebhookEvent.verify_and_parse(
            data=await request.body(),
            hexdigest=sig,
            webhook_secret=webhook_signing_key
        )

        if event.event_type == lightspark.WebhookEventType.PAYMENT_FINISHED:
            client = lightspark.LightsparkSyncClient(
                api_token_client_id=ls_client_id,
                api_token_client_secret=ls_secret,
            )
            entity_id = event.entity_id
            entity_class = lightspark.IncomingPayment
            
            payment = client.get_entity(entity_id, entity_class)

            if not payment:
                return JSONResponse({}, 200)

            payments = get_db()["payments"]
            payment_db = await payments.find_one({ "invoice_id": payment.payment_request_id })
            if not payment_db or payment_db["completed"]:
                return JSONResponse({}, 200)
            
            offer = get_offer_by_id(payment_db["offer_id"])
            if not offer:
                return JSONResponse({}, 200)
            
            users = get_db()["users"]
            await users.update_one({"user_id": payment_db["user_id"]}, { "$inc": { "balance": offer["balance"]} })
            await payments.update_one({ "invoice_id": payment.payment_request_id }, { "$set": { "completed": True }})
    except:
        pass

    return JSONResponse({}, 200)

@user.post("/set-as-paid")
async def set_as_paid(id: str):

    if os.getenv("ENV") != "development":
        return

    payments = get_db()["payments"]
    payment_db = await payments.find_one({"invoice_id": id})
    if not payment_db:
        return JSONResponse({"error": "Payment record not found"}, 404)
    if payment_db.get("completed", False):
        return JSONResponse({"status": "already paid"}, 200)

    offer = get_offer_by_id(payment_db["offer_id"])
    if not offer:
        return JSONResponse({"error": "Offer not found"}, 404)

    users = get_db()["users"]
    await users.update_one(
        {"user_id": payment_db["user_id"]},
        {"$inc": {"balance": offer["balance"]}}
    )
    await payments.update_one(
        {"invoice_id": id},
        {"$set": {"completed": True}}
    )

    return JSONResponse({"status": "Paid."}, 200)