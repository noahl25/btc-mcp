from fastapi import APIRouter, Body, Depends, Query, Request, HTTPException
from fastapi.responses import JSONResponse
from src.middleware.middleware import creator_session
from src.database.mongo import get_db
from dotenv import load_dotenv
from src.l402.l402 import create_lightning_invoice, get_offer_by_id, get_usd_amount_in_sats
from datetime import datetime, timezone, timedelta
import lightspark
import os
import bolt11
import asyncio

load_dotenv()

payments = APIRouter()

@payments.post("/top-up")
async def top_up(offer_id: str = Body(...), authorization_token: str = Body(...)):
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=5)
    invoice = await create_lightning_invoice(authorization_token, offer_id, expiry)
    if not invoice:
        raise HTTPException(400, "Invalid offer id.")
    return invoice

@payments.post("/stake")
async def stake(offer_id: str = Body(...), agent_id: str = Body(...), session = Depends(creator_session)):
    if not session:
        return JSONResponse({ "status": "failed", "message": "Not authenticated."}, 403)
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(minutes=5)
    invoice = await create_lightning_invoice(session["pubkey"], offer_id, expiry, agent_id=agent_id)
    if not invoice:
        return JSONResponse({ "status": "failed", "message": "Invalid offer id."}, 403)
    return invoice

@payments.post("/me")
async def me(session = Depends(creator_session)):
    if not session:
        return JSONResponse({ "status": "failed", "message": "Not authenticated"}, 403)
    
    stakes = get_db()["stakes"]
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    pipeline = [
        { "$match": { "pubkey": session["pubkey"], "date": { "$lt": seven_days_ago } } },
        { "$group": { "_id": None, "total": { "$sum": "$amount" } } }
    ]
    result = await (await stakes.aggregate(pipeline)).to_list(length=1)
    to_claim = result[0]["total"] if result else 0

    pipeline = [
        { "$match": { "pubkey": session["pubkey"] } },
        { "$group": { "_id": None, "total": { "$sum": "$amount" } } }
    ]
    result = await (await stakes.aggregate(pipeline)).to_list(length=1)
    total_staked = result[0]["total"] if result else 0

    return JSONResponse({
        "earnings": session["credits"],
        "staked": to_claim,
        "total_staked": total_staked
    }, 200)

@payments.post("/withdraw")
async def withdraw(session = Depends(creator_session), invoice: str = Body(..., embed=True)):
    if not session:
        return JSONResponse({ "status": "failed", "message": "Not authenticated"}, 403)
    
    ls_client_id = os.getenv("LIGHTSPARK_ID")
    ls_secret = os.getenv("LIGHTSPARK_SECRET")
    ls_node_id = os.getenv("LIGHTSPARK_NODE")
    ls_node_password = os.getenv("LIGHTSPARK_NODE_PASSWORD")

    if not ls_client_id or not ls_secret or not ls_node_id or not ls_node_password:
        return JSONResponse({}, 200)

    decoded = bolt11.decode(invoice)
    client = lightspark.LightsparkSyncClient(
        api_token_client_id=ls_client_id,
        api_token_client_secret=ls_secret,
    )
    signing_key = client.recover_node_signing_key(ls_node_id, ls_node_password)
    client.load_node_signing_key(ls_node_id, signing_key)
        
    stakes = get_db()["stakes"]
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    pipeline = [
        { "$match": { "pubkey": session["pubkey"], "date": { "$lt": seven_days_ago } } },
        { "$group": { "_id": None, "total": { "$sum": "$amount" } } }
    ]
    result = await (await stakes.aggregate(pipeline)).to_list(length=1)
    to_claim = result[0]["total"] if result else 0
    creators = get_db()["creators"]
    result = await creators.find_one({"pubkey": session["pubkey"] })
    to_claim += result["credits"] if result else 0

    if to_claim <= 0:
        return JSONResponse({ "status": "failed", "message": "Nothing to withdraw."}, 400)

    cents = to_claim / 20
    sats = await get_usd_amount_in_sats(int(cents))
    to_claim_msats = sats * 1000

    if to_claim_msats <= 0:
        return JSONResponse({ "status": "failed", "message": "Amount too small to withdraw."}, 400)

    if decoded.amount_msat or decoded.amount_msat == 0:
        return JSONResponse({ "status": "failed", "message": "Invoice should allow payer to specify amount."}, 400)

    outgoing = client.pay_invoice(
        node_id=ls_node_id,
        encoded_invoice=invoice,
        timeout_secs=60,
        maximum_fees_msats=500,
        amount_msats=to_claim_msats
    )

    for _ in range(30):
        if outgoing.status not in (lightspark.TransactionStatus.PENDING, lightspark.TransactionStatus.NOT_STARTED):  # type: ignore
            break
        await asyncio.sleep(2)
        outgoing = client.get_entity(outgoing.id, lightspark.OutgoingPayment) #type: ignore
    if outgoing.status == lightspark.TransactionStatus.SUCCESS: #type: ignore
        await stakes.delete_many({ "pubkey": session["pubkey"], "date": { "$lt": seven_days_ago } })
        await creators.update_one({ "pubkey": session["pubkey"] }, { "$set": { "credits": 0 } })
        return JSONResponse({ "status": "success"}, 200)
    else:
        return JSONResponse({ "status": "failed", "message": f"Payment failed. Status: {outgoing.status}, Reason: {outgoing.failure_reason}, Details: {outgoing.failure_message}"}, 500) #type: ignore


@payments.post("/webhook/lightspark")
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

            payments_collection = get_db()["payments"]
            payment_db = await payments_collection.find_one({ "invoice_id": payment.payment_request_id })
            if not payment_db or payment_db["completed"]:
                return JSONResponse({}, 200)
            
            offer = get_offer_by_id(payment_db["offer_id"])
            if not offer:
                return JSONResponse({}, 200)
            
            await payments_collection.update_one({ "invoice_id": payment.payment_request_id }, { "$set": { "completed": True }})
            if offer["type"] == "top-up":
                users = get_db()["users"]
                await users.update_one({"user_id": payment_db["user_id"]}, { "$inc": { "balance": offer["balance"]} })
            elif offer["type"] == "stake":
                stakes = get_db()["stakes"]
                await stakes.insert_one({ "pubkey": payment_db["user_id"], "amount": offer["balance"], "agentID": payment_db["agent_id"], "date": datetime.now(tz=timezone.utc) })
                agents = get_db()["agents"]
                await agents.update_one({ "id": payment_db["agent_id"] }, { "$inc": { "staked": offer["balance"] } })
            else:
                return JSONResponse({}, 500)
    except:
        pass

    return JSONResponse({}, 200)

@payments.get("/payment-complete/{id}")
async def payment_complete(id: str):
    payments_collection = get_db()["payments"]
    payment_db = await payments_collection.find_one({"invoice_id": id})
    return JSONResponse({ "status": payment_db["completed"] if payment_db else False }, 200)

@payments.get("/sats-to-usd/{amount}")
async def sats_to_usd(amount: int):
    return amount / await get_usd_amount_in_sats(1)

@payments.post("/set-as-paid")
async def set_as_paid(id: str):

    if os.getenv("ENV") != "development":
        return

    payments_collection = get_db()["payments"]
    payment_db = await payments_collection.find_one({"invoice_id": id})
    if not payment_db:
        return JSONResponse({"error": "Payment record not found"}, 404)
    if payment_db.get("completed", False):
        return JSONResponse({"status": "already paid"}, 200)

    offer = get_offer_by_id(payment_db["offer_id"])
    if not offer:
        return JSONResponse({"error": "Offer not found"}, 404)

    await payments_collection.update_one(
        {"invoice_id": id},
        {"$set": {"completed": True}}
    )

    if offer["type"] == "top-up":
        users = get_db()["users"]
        await users.update_one(
            {"user_id": payment_db["user_id"]},
            {"$inc": {"balance": offer["balance"]}}
        )
    elif offer["type"] == "stake":
        stakes = get_db()["stakes"]
        agents = get_db()["agents"]
        await agents.update_one({ "id": payment_db["agent_id"] }, { "$inc": { "staked": offer["balance"] } })
        await stakes.insert_one({ "pubkey": payment_db["user_id"], "amount": offer["balance"], "agent_id": payment_db["agent_id"], "date": datetime.now(tz=timezone.utc) })
    else:
        return JSONResponse({"error": "Unknown offer type"}, 500)

    return JSONResponse({"status": "Paid."}, 200)