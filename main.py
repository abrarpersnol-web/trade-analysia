import os
import hmac
import hashlib
import json
import requests
from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks, status, Query
from dotenv import load_dotenv

# .env file se variables load karein
load_dotenv()

app = FastAPI(title="Trade Analysia - Salla Backend Engine")

# Environment Variables
SALLA_CLIENT_ID = os.getenv("SALLA_CLIENT_ID")
SALLA_CLIENT_SECRET = os.getenv("SALLA_CLIENT_SECRET")
SALLA_REDIRECT_URI = os.getenv("SALLA_REDIRECT_URI")
SALLA_WEBHOOK_SECRET = os.getenv("SALLA_WEBHOOK_SECRET", SALLA_CLIENT_SECRET)

# -------------------------------------------------------------------
# Helper: Salla Webhook HMAC Signature Verify
# -------------------------------------------------------------------
def verify_salla_signature(raw_body: bytes, signature: str) -> bool:
    if not signature or not SALLA_WEBHOOK_SECRET:
        return False
    expected_sig = hmac.new(
        SALLA_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)

# -------------------------------------------------------------------
# Background Task: Order Event Worker
# -------------------------------------------------------------------
async def process_salla_event(event_name: str, merchant_id: str, data: dict):
    print(f"⚡ [WORKER] Event: '{event_name}' | Merchant: #{merchant_id}")

    if event_name == "order.created":
        order_id = data.get("id")
        total_price = data.get("amount", {}).get("amount", 0)
        currency = data.get("amount", {}).get("currency", "SAR")
        customer = data.get("customer", {}).get("first_name", "Valued Customer")
        
        print(f"🛒 New Order Received #{order_id} from {customer} | Total: {total_price} {currency}")
        # Yahan aap apna WhatsApp Alert / Database Save logic add kar sakte hain.

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.get("/")
def home():
    return {"status": "online", "app": "Trade Analysia Salla Engine"}

# 1. OAuth Callback Endpoint
@app.get("/oauth/callback")
async def salla_oauth_callback(code: str = Query(...)):
    token_url = "https://accounts.salla.sa/oauth2/token"
    payload = {
        "client_id": SALLA_CLIENT_ID,
        "client_secret": SALLA_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SALLA_REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"OAuth Failed: {response.text}")
        
    token_data = response.json()
    return {
        "status": "success",
        "message": "Merchant Authorized Successfully!",
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token")
    }

# 2. Salla Webhook Endpoint
@app.post("/webhook/salla", status_code=status.HTTP_200_OK)
async def handle_salla_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_salla_signature: str = Header(None, alias="X-Salla-Signature")
):
    body_bytes = await request.body()

    # Signature validation (Production Security)
    if x_salla_signature and not verify_salla_signature(body_bytes, x_salla_signature):
        raise HTTPException(status_code=401, detail="Invalid HMAC Signature")

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON Payload")

    event_type = payload.get("event")
    merchant = payload.get("merchant")
    event_data = payload.get("data", {})

    background_tasks.add_task(
        process_salla_event,
        event_name=event_type,
        merchant_id=str(merchant),
        data=event_data
    )

    return {"status": "success", "message": "Webhook acknowledged"}
